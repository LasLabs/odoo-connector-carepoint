# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )


_logger = logging.getLogger(__name__)


class CarepointSaleOrderLineNonRx(models.Model):
    """ Binding Model for the Carepoint Order Line """
    _name = 'carepoint.sale.order.line.non.rx'
    _inherit = 'carepoint.binding'
    _inherits = {'sale.order.line': 'odoo_id'}
    _description = 'Carepoint NonRx Order Line'
    # Name of model in Carepoint lib (snake_case)
    _cp_lib = 'order_line_non_rx'

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

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['order_id'],
                                'carepoint.sale.order')
