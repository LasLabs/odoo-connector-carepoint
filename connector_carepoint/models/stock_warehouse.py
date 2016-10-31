# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..backend import carepoint
from ..unit.mapper import CarepointImportMapper, trim
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class StockWarehouse(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'stock.warehouse'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.stock.warehouse',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointStockWarehouse(models.Model):
    """ Binding Model for the Carepoint Warehouse """
    _name = 'carepoint.stock.warehouse'
    _inherit = 'carepoint.binding'
    _inherits = {'stock.warehouse': 'odoo_id'}
    _description = 'Carepoint Warehouse'
    _cp_lib = 'store'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Company',
        required=True,
        ondelete='cascade'
    )


@carepoint
class StockWarehouseAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Store """
    _model_name = 'carepoint.stock.warehouse'


@carepoint
class StockWarehouseBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Stores.
    For every company in the list, a delayed job is created.
    """
    _model_name = ['carepoint.stock.warehouse']


@carepoint
class StockWarehouseImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.stock.warehouse'

    direct = [
        (trim('name'), 'name'),
    ]

    @mapping
    @only_create
    def code(self, record):
        return {'code': record['name'].strip()}

    @mapping
    def is_pharmacy(self, record):
        return {'is_pharmacy': True}

    @mapping
    @only_create
    def partner_id(self, record):
        binder = self.binder_for('carepoint.carepoint.store')
        pharmacy_id = binder.to_odoo(record['store_id'], browse=True)
        return {
            'partner_id': pharmacy_id.partner_id.id,
        }

    @mapping
    @only_create
    def route_ids(self, record):
        """ It returns the RX & OTC route ids """
        module = 'sale_stock_medical_prescription'
        rx_route_id = self.env.ref(
            '%s.route_warehouse0_prescription' % module
        )
        otc_route_id = self.env.ref(
            '%s.route_warehouse0_otc' % module
        )
        return {
            'route_ids': [(6, 0, [rx_route_id.id, otc_route_id.id])],
            'prescription_route_id': rx_route_id.id,
            'otc_route_id': otc_route_id.id,
        }

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['store_id']}


@carepoint
class StockWarehouseImporter(CarepointImporter):
    _model_name = ['carepoint.stock.warehouse']
    _base_mapper = StockWarehouseImportMapper
