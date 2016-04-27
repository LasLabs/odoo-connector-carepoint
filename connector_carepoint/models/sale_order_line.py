# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  changed_by,
                                                  only_create,
                                                  ExportMapper,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..connector import get_environment
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import (CarepointExporter)
from ..unit.delete_synchronizer import (CarepointDeleter)
from ..connector import add_checkpoint, get_environment
from ..related_action import unwrap_binding


_logger = logging.getLogger(__name__)


class CarepointSaleOrderLine(models.Model):
    """ Binding Model for the Carepoint Order Line """
    _name = 'carepoint.sale.order.line'
    _inherit = 'carepoint.binding'
    _inherits = {'sale.order.line': 'odoo_id'}
    _description = 'Carepoint Rx Dispense'
    _cp_lib = 'dispense'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Company',
        required=True,
        ondelete='cascade'
    )
    backend_id = fields.Many2one(
        comodel_name='carepoint.backend',
        string='Carepoint Backend',
        store=True,
        readonly=True,
        # override 'carepoint.binding', can't be INSERTed if True:
        required=False,
    )
    created_at = fields.Date('Created At (on Carepoint)')
    updated_at = fields.Date('Updated At (on Carepoint)')

    _sql_constraints = [
        ('odoo_uniq', 'unique(backend_id, odoo_id)',
         'A Carepoint binding for this order already exists.'),
    ]


class SaleOrderLine(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'sale.order.line'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.sale.order.line',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class SaleOrderLineAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Order Line """
    _model_name = 'carepoint.sale.order.line'


@carepoint
class SaleOrderLineBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Order Lines.
    For every order in the list, a delayed job is created.
    """
    _model_name = ['carepoint.sale.order.line']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class SaleOrderLineImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.sale.order.line'

    direct = [
        ('submit_date', 'date_order'),
        ('dispense_qty', 'product_uom_qty'),
    ]

    @mapping
    def prescription_data(self, record):
        binder = self.binder_for('carepoint.medical.prescription.order')
        rx_id = self.env['carepoint.medical.prescription.order'].browse(
            binder.to_odoo(record['rx_id'])
        )
        line_id = rx_id.prescription_order_line_ids[0]
        return {
            'prescription_order_line_id': line_id.id,
            'patient_id': rx_id.patient_id.id,
        }

    @mapping
    def order_id(self, record):
        binder = self.binder_for('carepoint.sale.order')
        order_id = binder.to_odoo(record['order_id'])

    @mapping
    def product_data(self, record):
        binder = self.binder_for('carepoint.medical.medicament')
        med_id = self.env['carepoint.medical.medicament'].browse(
            binder.to_odoo(record['item_id'])
        )
        return {
            'product_id': med_id.product_id.id,
            'product_uom': line_id.medicament_id.uom_id.id,
        }

    @mapping
    def price_unit(self, record):
        # @TODO: Figure out where the prices are
        return {'price_unit': 0}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['rxdisp_id']}


@carepoint
class SaleOrderLineImporter(CarepointImporter):
    _model_name = ['carepoint.sale.order.line']

    _base_mapper = SaleOrderLineImportMapper

    def _create(self, data):
        binding = super(SaleOrderLineImporter, self)._create(data)
        checkpoint = self.unit_for(SaleOrderLineAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['rx_id'],
                                'carepoint.medical.prescription')
        self._import_dependency(record['order_id'],
                                'carepoint.sale.order')

    #
    # def _after_import(self, partner_binding):
    #     """ Import the addresses """
    #     book = self.unit_for(PartnerAddressBook, model='carepoint.address')
    #     book.import_addresses(self.carepoint_id, partner_binding.id)


@carepoint
class SaleOrderLineExportMapper(ExportMapper):
    _model_name = 'carepoint.sale.order.line'

    direct = [
        ('ref', 'ssn'),
        ('email', 'email'),
        ('dob', 'birth_date'),
        ('dod', 'death_date'),
    ]

    @mapping
    def pat_id(self, record):
        return {'pat_id': record.carepoint_id}

    @changed_by('gender')
    @mapping
    def gender_cd(self):
        return {'gender_cd': record.get('gender').upper()}


@carepoint
class SaleOrderLineExporter(CarepointExporter):
    _model_name = ['carepoint.sale.order.line']
    _base_mapper = SaleOrderLineExportMapper


@carepoint
class SaleOrderLineDeleteSynchronizer(CarepointDeleter):
    _model_name = ['carepoint.sale.order.line']


@carepoint
class SaleOrderLineAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.sale.order.line record """
    _model_name = ['carepoint.sale.order.line', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint')
def order_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of orders modified on Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(SaleOrderLineBatchImporter)
    importer.run(filters=filters)
