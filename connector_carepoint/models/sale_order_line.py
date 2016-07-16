# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
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
from ..connector import add_checkpoint
from .procurement_order import ProcurementOrderUnit


_logger = logging.getLogger(__name__)


class CarepointSaleOrderLine(models.Model):
    """ Binding Model for the Carepoint Order Line """
    _name = 'carepoint.sale.order.line'
    _inherit = 'carepoint.binding'
    _inherits = {'sale.order.line': 'odoo_id'}
    _description = 'Carepoint Rx Order Line'
    _cp_lib = 'order_line'  # Name of model in Carepoint lib (snake_case)

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
class SaleOrderLineUnit(ConnectorUnit):
    _model_name = 'carepoint.sale.order.line'

    def __get_order_lines(self, sale_order_id):
        adapter = self.unit_for(CarepointCRUDAdapter)
        return adapter.search(order_id=sale_order_id)

    def _import_sale_order_lines(self, sale_order_id):
        importer = self.unit_for(SaleOrderLineImporter)
        for rec_id in self.__get_order_lines(sale_order_id):
            importer.run(rec_id)

    def _get_order_line_count(self, sale_order_id):
        return len(self.__get_order_lines(sale_order_id))


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

    direct = []

    @mapping
    @only_create
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
    @only_create
    def tax_id(self, record):
        return {'tax_id': [(4, self.backend_record.default_sale_tax.id)]}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['line_id']}


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
                                'carepoint.medical.prescription.order.line')
        self._import_dependency(record['order_id'],
                                'carepoint.sale.order')

    def _after_import(self, binding):
        record = self.carepoint_record
        self._import_dependency(record['rxdisp_id'],
                                'carepoint.procurement.order')
        self._import_dependency(record['rxdisp_id'],
                                'carepoint.account.invoice.line')
        proc_unit = self.unit_for(
            ProcurementOrderUnit, model='carepoint.procurement.order',
        )
        binder = self.binder_for('carepoint.sale.order')
        order_id = binder.to_backend(binding.order_id)
        line_cnt = proc_unit._get_order_line_count(
            order_id
        )
        if len(binding.order_id.order_line) == line_cnt:
            self._import_dependency(
                record['order_id'], 'carepoint.stock.picking'
            )


@carepoint
class SaleOrderLineAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.sale.order.line record """
    _model_name = ['carepoint.sale.order.line', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)
