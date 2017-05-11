# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               ExportMapper,
                                               only_create,
                                               m2o_to_backend,
                                               )
from odoo.addons.connector.connector import ConnectorUnit
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (CarepointImportMapper,
                           CommonDateExportMapperMixer,
                           CommonDateImporterMixer,
                           CommonDateImportMapperMixer,
                           )
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import CarepointExporter

from .procurement_order import ProcurementOrderUnit


_logger = logging.getLogger(__name__)


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
    rx_disp_external = fields.Char()

    _sql_constraints = [
        ('rx_disp_external_unique', 'UNIQUE(rx_disp_external)',
         'Carepoint Rx Dispense can only be assigned to one sale order line'),
    ]


@carepoint
class SaleOrderLineAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Order Line """
    _model_name = 'carepoint.sale.order.line'


@carepoint
class SaleOrderLineUnit(ConnectorUnit):
    _model_name = 'carepoint.sale.order.line'

    def _get_order_lines(self, sale_order_id):
        adapter = self.unit_for(CarepointCRUDAdapter)
        return adapter.search(order_id=sale_order_id)

    def _import_sale_order_lines(self, sale_order_id):
        importer = self.unit_for(SaleOrderLineImporter)
        for rec_id in self._get_order_lines(sale_order_id):
            importer.run(rec_id)

    def _get_order_line_count(self, sale_order_id):
        return len(self._get_order_lines(sale_order_id))


@carepoint
class SaleOrderLineBatchImporter(DelayedBatchImporter,
                                 CommonDateImporterMixer):
    """ Import the Carepoint Order Lines.
    For every order in the list, a delayed job is created.
    """
    _model_name = ['carepoint.sale.order.line']


@carepoint
class SaleOrderLineImportMapper(CarepointImportMapper,
                                CommonDateImportMapperMixer):
    _model_name = 'carepoint.sale.order.line'

    direct = [
        ('rxdisp_id', 'rx_disp_external'),
    ]

    @mapping
    @only_create
    def prescription_data(self, record):
        binder = self.binder_for('carepoint.rx.ord.ln')
        line_id = binder.to_odoo(record['rx_id'], browse=True)
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
        # @TODO: Are prices even possible in sales? Seems only after dispense
        return {'price_unit': 0}

    @mapping
    @only_create
    def tax_id(self, record):
        return {'tax_id': [(4, self.backend_record.default_sale_tax.id)]}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['line_id']}


@carepoint
class SaleOrderLineImporter(CarepointImporter,
                            CommonDateImporterMixer):
    _model_name = ['carepoint.sale.order.line']

    _base_mapper = SaleOrderLineImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['rx_id'],
                                'carepoint.rx.ord.ln')
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
            try:
                self._import_dependency(
                    record['order_id'], 'carepoint.stock.picking'
                )
            except IndexError:
                _logger.debug('No pickings exist for order %s', order_id)


@carepoint
class SaleOrderLineExportMapper(ExportMapper,
                                CommonDateExportMapperMixer):
    _model_name = 'carepoint.sale.order.line'

    direct = [
        (m2o_to_backend('prescription_order_line_id',
                        binding='carepoint.rx.ord.ln'),
         'rx_id'),
        (m2o_to_backend('order_id', binding='carepoint.sale.order'),
         'order_id'),
    ]


@carepoint
class SaleOrderLineExporter(CarepointExporter):
    _model_name = ['carepoint.sale.order.line']
    _base_mapper = SaleOrderLineExportMapper

    def _export_dependencies(self):
        self._export_dependency(
            self.binding_record.order_id,
            'carepoint.sale.order',
        )
        self._export_dependency(
            self.binding_record.prescription_order_line_id,
            'carepoint.rx.ord.ln',
        )
