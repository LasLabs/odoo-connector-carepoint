# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, models, fields
from odoo.addons.connector.connector import ConnectorUnit
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               m2o_to_backend,
                                               follow_m2o_relations,
                                               ExportMapper,
                                               )
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


_logger = logging.getLogger(__name__)


class ProcurementOrder(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'procurement.order'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.procurement.order',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointProcurementOrder(models.Model):
    """ Binding Model for the Carepoint Patient """
    _name = 'carepoint.procurement.order'
    _inherit = 'carepoint.binding'
    _inherits = {'procurement.order': 'odoo_id'}
    _description = 'Carepoint Dispense'
    _cp_lib = 'dispense'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='procurement.order',
        string='Company',
        required=True,
        ondelete='cascade',
    )
    prescription_order_line_id = fields.Many2one(
        string='Prescription Line',
        comodel_name='medical.prescription.order.line',
        related='sale_line_id.prescription_order_line_id',
    )
    carepoint_store_id = fields.Many2one(
        string='Carepoint Store',
        comodel_name='carepoint.store',
        compute='_compute_carepoint_store_id',
        store=True,
    )

    @api.multi
    @api.depends(
        'prescription_order_line_id.prescription_order_id.partner_id',
    )
    def _compute_carepoint_store_id(self):
        for rec_id in self:
            rx_order = rec_id.prescription_order_line_id.prescription_order_id
            store = self.env['carepoint.store'].get_by_pharmacy(
                rx_order.partner_id,
            )
            rec_id.carepoint_store_id = store.id


@carepoint
class ProcurementOrderAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Patient """
    _model_name = 'carepoint.procurement.order'


@carepoint
class ProcurementOrderUnit(ConnectorUnit):
    _model_name = 'carepoint.procurement.order'

    def _get_order_lines(self, sale_order_id):
        adapter = self.unit_for(CarepointCRUDAdapter)
        return adapter.search(order_id=sale_order_id)

    def _import_procurements_for_sale(self, sale_order_id):
        importer = self.unit_for(ProcurementOrderImporter)
        for rec_id in self._get_order_lines(sale_order_id):
            importer.run(rec_id)

    def _get_order_line_count(self, sale_order_id):
        return len(self._get_order_lines(sale_order_id))


@carepoint
class ProcurementOrderBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Patients.
    For every patient in the list, a delayed job is created.
    """
    _model_name = ['carepoint.procurement.order']


@carepoint
class ProcurementOrderImportMapper(CarepointImportMapper,
                                   CommonDateImportMapperMixer):
    _model_name = 'carepoint.procurement.order'

    direct = [
        ('dispense_qty', 'product_qty'),
        ('dispense_date', 'date_planned'),
    ]

    @mapping
    def name(self, record):
        binder = self.binder_for('carepoint.rx.ord.ln')
        rx_id = binder.to_odoo(record['rx_id'], browse=True)
        name = 'RX %s - %s' % (record['rx_id'],
                               rx_id.medicament_id.display_name)
        return {'name': name}

    @mapping
    @only_create
    def order_line_procurement_data(self, record):

        binder = self.binder_for('carepoint.rx.ord.ln')
        rx_id = binder.to_odoo(record['rx_id'], browse=True)
        binder = self.binder_for('carepoint.fdb.ndc')
        ndc_id = binder.to_odoo(record['disp_ndc'].strip(), browse=True)
        line_id = self.env['carepoint.sale.order.line'].search([
            ('rx_disp_external', '=', record['rxdisp_id']),
        ])
        line_id = line_id.odoo_id
        sale_id = line_id.order_id
        _logger.debug('Got %s from %s, %s, %s', line_id, sale_id, sale_id.order_line, record.__dict__)
        line_id = line_id.with_context(connector_no_export=True)

        # Set the sale line to what was dispensed
        # This is a hack circumventing lack of qty in CP until now
        line_id.write({
            'product_id': ndc_id.medicament_id.product_id.id,
            'product_uom_qty': float(record['dispense_qty']),
        })

        procurement_group_id = self.env['procurement.group'].search([
            ('name', '=', sale_id.name),
        ],
            limit=1,
        )
        if not len(procurement_group_id):
            procurement_group_id = self.env['procurement.group'].create(
                sale_id._prepare_procurement_group()
            )
            sale_id.procurement_group_id = procurement_group_id.id

        res = line_id._prepare_order_line_procurement(procurement_group_id.id)
        res.update({'origin': sale_id.name,
                    'product_uom': line_id.product_uom.id,
                    'ndc_id': ndc_id.id,
                    'product_id': line_id.product_id.id,
                    })

        return res

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['rxdisp_id']}


@carepoint
class ProcurementOrderImporter(CarepointImporter,
                               CommonDateImporterMixer):
    _model_name = ['carepoint.procurement.order']

    _base_mapper = ProcurementOrderImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['rx_id'],
                                'carepoint.rx.ord.ln')
        self._import_dependency(record['disp_ndc'].strip(),
                                'carepoint.fdb.ndc')
        self._import_dependency(record['order_id'],
                                'carepoint.sale.order')

    # def _after_import(self, binding):
        # """ Import the stock pickings & invoice lines if all lines
        #     imported
        # """
        # self.binder_for('carepoint.sale.order')
        # sale_id = binder.to_odoo(self.carepoint_record['order_id'])
        # proc_unit = self.unit_for(
        #     ProcurementOrderUnit, model='carepoint.procurement.order',
        # )
        # proc_unit._get_order_line_count(self.carepoint_record['order_id'])
        # if len(binding.sale_line_id.order_id.order_line) == line_cnt:
        #     record = self.carepoint_record
        #     picking_unit = self.unit_for(
        #         StockPickingUnit, model='carepoint.stock.picking',
        #     )
        #     order_bind_id = binder.to_backend(
        #         binding.sale_line_id.order_id.id, wrap=False,
        #     )
        #     picking_unit._import_pickings_for_sale(order_bind_id)
        # invoice_unit = self.unit_for(
        #     AccountInvoiceLineUnit, model='carepoint.account.invoice.line',
        # )
        # invoice_unit._import_invoice_lines_for_procurement(
        #     record['rxdisp_id'], binding.id,
        # )


@carepoint
class ProcurementOrderLineExportMapper(ExportMapper,
                                       CommonDateExportMapperMixer):
    _model_name = 'carepoint.procurement.order'

    direct = [
        (m2o_to_backend('prescription_order_line_id',
                       binding='carepoint.rx.ord.ln'),
         'rx_id'),
        (m2o_to_backend('carepoint_store_id',
                        binding='carepoint.carepoint.store'),
         'store_id'),
        (follow_m2o_relations('ndc_id.name'), 'disp_ndc'),
        (follow_m2o_relations('ndc_id.medicament_id.display_name'),
         'disp_drug_name'),
        (follow_m2o_relations('ndc_id.manufacturer_id.name'), 'mfg'),
        (follow_m2o_relations('prescription_order_line_id.'
                              'medication_dosage_id.name'),
         'sig_text'),
        (follow_m2o_relations('prescription_order_line_id.quantity'),
         'units_per_dose'),
        (follow_m2o_relations('prescription_order_line_id.frequency'),
         'freq_of_admin'),
        (follow_m2o_relations('ndc_id.medicament_id.gpi'), 'gpi_disp'),
        ('product_qty', 'pkg_size'),
        ('date_planned', 'dispense_date'),
        ('product_qty', 'dispense_qty'),
    ]

    @mapping
    def static_defaults(self, record):
        return {'status_cn': 0,
                'label_3pty_yn': 4,
                'reject_3pty_yn': 0,
                }


@carepoint
class ProcurementOrderLineExporter(CarepointExporter):
    _model_name = ['carepoint.procurement.order']
    _base_mapper = ProcurementOrderLineExportMapper

    def _export_dependencies(self):
        self._export_dependency(
            self.binding_record.sale_line_id.prescription_order_line_id,
            'carepoint.rx.ord.ln',
        )
        self._export_dependency(
            self.binding_record.sale_line_id,
            'carepoint.sale.order.line',
        )
