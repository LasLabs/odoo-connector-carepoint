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
from .address import AddressUnit


_logger = logging.getLogger(__name__)


class CarepointStockPicking(models.Model):
    """ Binding Model for the Carepoint Shipment """
    _name = 'carepoint.stock.picking'
    _inherit = 'carepoint.binding'
    _inherits = {'stock.picking': 'odoo_id'}
    _description = 'Carepoint Shipment'
    _cp_lib = 'order_ship'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Company',
        required=True,
        ondelete='cascade',
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
         'A Carepoint binding for this patient already exists.'),
    ]


class StockPicking(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'stock.picking'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.stock.picking',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class StockPickingAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Patient """
    _model_name = 'carepoint.stock.picking'


@carepoint
class StockPickingUnit(ConnectorUnit):
    _model_name = 'carepoint.stock.picking'

    def _import_pickings_for_sale(self, sale_order_id, binding_id):
        adapter = self.unit_for(CarepointCRUDAdapter)
        importer = self.unit_for(StockPickingImporter)
        rec_ids = adapter.search(order_id=sale_order_id)
        for rec_id in rec_ids:
            importer.run(rec_id)


@carepoint
class StockPickingBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Patients.
    For every patient in the list, a delayed job is created.
    """
    _model_name = ['carepoint.stock.picking']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class StockPickingImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.stock.picking'

    direct = [
        ('tracking_code', 'carrier_tracking_ref'),
    ]

    @mapping
    @only_create
    def odoo_id(self, record):
        binder = self.binder_for('carepoint.sale.order')
        order_id = binder.to_odoo(record['order_id'], browse=True)
        _logger.debug('FUCK %s', order_id.picking_ids)
        return {'odoo_id': order_id.picking_ids[0]}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['order_id']}


@carepoint
class StockPickingImporter(CarepointImporter):
    _model_name = ['carepoint.stock.picking']

    _base_mapper = StockPickingImportMapper

    def _create(self, data):
        binding = super(StockPickingImporter, self)._create(data)
        checkpoint = self.unit_for(StockPickingAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['rx_id'],
                                'carepoint.medical.prescription.order.line')
        self._import_dependency(record['order_id'],
                                'carepoint.sale.order')
        # unit = self.unit_for(
        #     AddressUnit, model='carepoint.carepoint.address.patient',
        # )
        # unit._import_by_filter(
        #     addr1=record['bill_addr1'],
        #     addr2=record['bill_addr2'],
        #     city=record['bill_city'],
        #     state_cd=record['bill_state_cd'],
        #     zip=record['bill_zip'],
        # )
        # unit._import_by_filter(
        #     addr1=record['ship_addr1'],
        #     addr2=record['ship_addr2'],
        #     city=record['ship_city'],
        #     state_cd=record['ship_state_cd'],
        #     zip=record['ship_zip'],
        # )

    def _after_import(self, binding):
        binding.action_done()


@carepoint
class StockPickingExportMapper(ExportMapper):
    _model_name = 'carepoint.stock.picking'

    direct = [
        ('ref', 'ssn'),
        ('email', 'email'),
        ('dob', 'birth_date'),
        ('dod', 'death_date'),
    ]

    @mapping
    def pat_id(self, record):
        return {'pat_id': record.carepoint_id}

    @mapping
    @changed_by('gender')
    def gender_cd(self):
        return {'gender_cd': record.get('gender').upper()}


@carepoint
class StockPickingExporter(CarepointExporter):
    _model_name = ['carepoint.stock.picking']
    _base_mapper = StockPickingExportMapper


@carepoint
class StockPickingAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.stock.picking record """
    _model_name = ['carepoint.stock.picking', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.patient')
def patient_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of patients modified on Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(StockPickingBatchImporter)
    importer.run(filters=filters)
