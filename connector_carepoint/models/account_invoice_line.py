# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.connector import ConnectorUnit
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               ExportMapper,
                                               )
from ..unit.backend_adapter import CarepointAdapter
from ..unit.mapper import CarepointImportMapper
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import (CarepointExporter)
from ..unit.delete_synchronizer import (CarepointDeleter)
from .procurement_order import ProcurementOrderUnit


_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'account.invoice.line'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.account.invoice.line',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointAccountInvoiceLine(models.Model):
    """ Binding Model for the Carepoint Invoice Line """
    _name = 'carepoint.account.invoice.line'
    _inherit = 'carepoint.binding'
    _inherits = {'account.invoice.line': 'odoo_id'}
    _description = 'Carepoint Account Invoice Line'
    _cp_lib = 'dispense_price'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class AccountInvoiceLineAdapter(CarepointAdapter):
    """ Backend Adapter for the Carepoint Patient """
    _model_name = 'carepoint.account.invoice.line'


class AccountInvoiceLineUnit(ConnectorUnit):
    # @TODO: Move this somewhere else, here due to circular import issue
    _model_name = 'carepoint.account.invoice.line'

    def _import_invoice_lines_for_procurement(self, rxdisp_id):
        adapter = self.unit_for(CarepointAdapter)
        importer = self.unit_for(AccountInvoiceLineImporter)
        rec_ids = adapter.search(rxdisp_id=rxdisp_id)
        for rec_id in rec_ids:
            importer.run(rec_id)


class AccountInvoiceLineBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Patients.
    For every order in the list, a delayed job is created.
    """
    _model_name = ['carepoint.account.invoice.line']


class AccountInvoiceLineImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.account.invoice.line'

    @mapping
    @only_create
    def invoice_id(self, record):
        binder = self.binder_for('carepoint.procurement.order')
        proc_id = binder.to_odoo(record['rxdisp_id'], browse=True)
        invoice_id = self.env['account.invoice'].search([
            ('origin', '=', proc_id.sale_line_id.order_id.name)
        ],
            limit=1,
        )
        if len(invoice_id):
            invoice_id = invoice_id[0]
        else:
            vals = proc_id.sale_line_id.order_id._prepare_invoice()
            vals.update({
                'date_invoice': record['primary_pay_date'],
            })
            invoice_id = self.env['account.invoice'].create(vals)
        return {'invoice_id': invoice_id.id}

    @mapping
    @only_create
    def sale_line_ids(self, record):
        binder = self.binder_for('carepoint.procurement.order')
        proc_id = binder.to_odoo(record['rxdisp_id'], browse=True)
        return {
            'sale_line_ids': [(6, 0, [proc_id.sale_line_id.id])],
        }

    @mapping
    def invoice_line_data(self, record):
        binder = self.binder_for('carepoint.procurement.order')
        proc_id = binder.to_odoo(record['rxdisp_id'], browse=True)
        line_id = proc_id.sale_line_id
        qty = line_id.product_uom_qty
        line_id.price_unit = float(record['t_patient_pay_sub']) / qty
        res = line_id._prepare_invoice_line(qty)
        return res

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['rxdisp_id']}


class AccountInvoiceLineImporter(CarepointImporter):
    _model_name = ['carepoint.account.invoice.line']

    _base_mapper = AccountInvoiceLineImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['rxdisp_id'],
                                'carepoint.procurement.order')

    def _after_import(self, binding):
        """ Validate and pay if necessary """
        binder = self.binder_for('carepoint.procurement.order')
        proc_id = binder.to_odoo(self.carepoint_record['rxdisp_id'],
                                 browse=True)
        binder = self.binder_for('carepoint.sale.order')
        sale_id = binder.to_backend(proc_id.sale_line_id.order_id.id)
        proc_unit = self.unit_for(
            ProcurementOrderUnit, model='carepoint.procurement.order',
        )
        line_cnt = proc_unit._get_order_line_count(sale_id)
        invoice_id = self._get_binding().invoice_id
        if len(invoice_id.invoice_line_ids) == line_cnt:
            cp_state = proc_id.sale_line_id.order_id.carepoint_order_state_cn
            state_id = self.env.ref(
                'connector_carepoint.state_%d' % cp_state
            )
            vals = {}
            if invoice_id.state != state_id.invoice_state:
                vals['state'] = state_id.invoice_state
            if state_id.invoice_state == 'paid':
                if invoice_id.state != 'paid':
                    invoice_id.action_move_create()
                    invoice_id.invoice_validate()
                    if invoice_id.residual > 0:
                        invoice_id.pay_and_reconcile(
                            self.backend_record.default_payment_journal,
                            date=invoice_id.date_invoice,
                        )
            invoice_id.write(vals)


class AccountInvoiceLineExportMapper(ExportMapper):
    _model_name = 'carepoint.account.invoice.line'


class AccountInvoiceLineExporter(CarepointExporter):
    _model_name = ['carepoint.account.invoice.line']
    _base_mapper = AccountInvoiceLineExportMapper


class AccountInvoiceLineDeleteSynchronizer(CarepointDeleter):
    _model_name = ['carepoint.account.invoice.line']
