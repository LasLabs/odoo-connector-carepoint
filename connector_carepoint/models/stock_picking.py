# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )


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

    def _import_pickings_for_sale(self, sale_order_id):
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
        picking_ids = order_id.picking_ids
        return {'odoo_id': picking_ids[0].id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['order_id']}


@carepoint
class StockPickingImporter(CarepointImporter):
    _model_name = ['carepoint.stock.picking']

    _base_mapper = StockPickingImportMapper

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
        """ Transfer pickings and trigger invoice generation """

        binding.odoo_id.force_assign()
        wiz_id = self.env['stock.immediate.transfer'].create({
            'pick_id': binding.odoo_id.id
        })
        wiz_id.process()
