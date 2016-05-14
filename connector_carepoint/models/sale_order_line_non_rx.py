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


class CarepointSaleOrderLineNonRx(models.Model):
    """ Binding Model for the Carepoint Order Line """
    _name = 'carepoint.sale.order.line.non.rx'
    _inherit = 'carepoint.binding'
    _inherits = {'sale.order.line': 'odoo_id'}
    _description = 'Carepoint NonRx Order Line'
    _cp_lib = 'order_line_non_rx'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Order Line',
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


class SaleOrderLineNonRx(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'sale.order.line'

    carepoint_nonrx_bind_ids = fields.One2many(
        comodel_name='carepoint.sale.order.line.non.rx',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class SaleOrderLineNonRxAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Order Line """
    _model_name = 'carepoint.sale.order.line.non.rx'


@carepoint
class SaleOrderLineNonRxUnit(ConnectorUnit):
    _model_name = 'carepoint.sale.order.line.non.rx'

    def _import_sale_order_lines(self, sale_order_id, sale_order_binding_id):
        adapter = self.unit_for(CarepointCRUDAdapter)
        importer = self.unit_for(SaleOrderLineNonRxImporter)
        sale_line_ids = adapter.search(order_id=sale_order_id)
        for rec_id in sale_line_ids:
            importer.run(rec_id)

@carepoint
class SaleOrderLineNonRxBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Order Lines.
    For every order in the list, a delayed job is created.
    """
    _model_name = ['carepoint.sale.order.line.non.rx']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class SaleOrderLineNonRxImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.sale.order.line.non.rx'

    direct = []

    @mapping
    def prescription_data(self, record):
        binder = self.binder_for('carepoint.medical.prescription.order.line')
        line_id = self.env['medical.prescription.order.line'].browse(
            binder.to_odoo(record['rx_id'])
        )
        return {'prescription_order_line_id': line_id.id,
                'product_id': line_id.medicament_id.product_id.id,
                'product_uom': line_id.dispense_uom_id.id,
                'product_uom_qty': line_id.qty,
                'name': line_id.medicament_id.display_name,
                }

    @mapping
    def order_id(self, record):
        binder = self.binder_for('carepoint.sale.order')
        order_id = binder.to_odoo(record['order_id'])
        return {'order_id': order_id}

    @mapping
    def price_unit(self, record):
        # @TODO: Figure out where the prices are
        return {'price_unit': 0}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['line_id']}


@carepoint
class SaleOrderLineNonRxImporter(CarepointImporter):
    _model_name = ['carepoint.sale.order.line.non.rx']

    _base_mapper = SaleOrderLineNonRxImportMapper

    def _create(self, data):
        binding = super(SaleOrderLineNonRxImporter, self)._create(data)
        checkpoint = self.unit_for(SaleOrderLineNonRxAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['order_id'],
                                'carepoint.sale.order')


@carepoint
class SaleOrderLineNonRxExportMapper(ExportMapper):
    _model_name = 'carepoint.sale.order.line.non.rx'

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
class SaleOrderLineNonRxExporter(CarepointExporter):
    _model_name = ['carepoint.sale.order.line.non.rx']
    _base_mapper = SaleOrderLineNonRxExportMapper


@carepoint
class SaleOrderLineNonRxDeleteSynchronizer(CarepointDeleter):
    _model_name = ['carepoint.sale.order.line.non.rx']


@carepoint
class SaleOrderLineNonRxAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.sale.order.line.non.rx record """
    _model_name = ['carepoint.sale.order.line.non.rx', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)
