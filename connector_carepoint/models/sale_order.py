# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.addons.connector_v9.unit.mapper import (mapping,
                                               m2o_to_backend,
                                               only_create,
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
from .carepoint_account import CarepointAccountUnit

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'sale.order'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.sale.order',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )
    carepoint_order_state_cn = fields.Integer('State Code in CP')


class CarepointSaleOrder(models.Model):
    """ Binding Model for the Carepoint Patient """
    _name = 'carepoint.sale.order'
    _inherit = 'carepoint.binding'
    _inherits = {'sale.order': 'odoo_id'}
    _description = 'Carepoint Sale'
    _cp_lib = 'order'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='sale.order',
        string='Company',
        required=True,
        ondelete='cascade'
    )
    prescription_order_line_id = fields.Many2one(
        string='Prescription Line',
        comodel_name='medical.prescription.order.line',
        compute='_compute_prescription_order_line_id',
        store=True,
    )
    pharmacy_id = fields.Many2one(
        string='Pharmacy',
        comodel_name='medical.pharmacy',
        related='prescription_order_line_id.prescription_order_id.partner_id',
    )
    carepoint_store_id = fields.Many2one(
        string='Carepoint Store',
        comodel_name='carepoint.store',
        compute='_compute_carepoint_store_id',
        store=True,
    )
    carepoint_account_id = fields.Many2one(
        string='Carepoint Account',
        comodel_name='carepoint.account',
        compute='_compute_carepoint_account_id',
        store=True,
    )

    @api.multi
    @api.depends('order_line.prescription_order_line_id')
    def _compute_prescription_order_line_id(self):
        for record in self:
            try:
                sale_line = record.order_line[0]
            except IndexError:
                continue
            rx_line = sale_line.prescription_order_line_id
            record.prescription_order_line_id = rx_line.id

    @api.multi
    @api.depends('partner_id')
    def _compute_carepoint_store_id(self):
        for record in self:
            store = self.env['carepoint.store'].get_by_pharmacy(
                record.pharmacy_id,
            )
            record.carepoint_store_id = store.id

    @api.multi
    @api.depends('prescription_order_line_id.patient_id')
    def _compute_carepoint_account_id(self):
        for record in self:
            account = self.env['carepoint.account']._get_by_patient(
                record.prescription_order_line_id.patient_id
            )
            record.carepoint_account_id = account.id


@carepoint
class SaleOrderAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Patient """
    _model_name = 'carepoint.sale.order'


@carepoint
class SaleOrderBatchImporter(DelayedBatchImporter,
                             CommonDateImporterMixer):
    """ Import the Carepoint Patients.
    For every order in the list, a delayed job is created.
    """
    _model_name = ['carepoint.sale.order']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class SaleOrderImportMapper(CarepointImportMapper,
                            CommonDateImportMapperMixer):
    _model_name = 'carepoint.sale.order'

    direct = [
        ('comments', 'note'),
    ]

    @mapping
    def name(self, record):
        name = '{prefix}{name}'.format(
            prefix=self.backend_record.sale_prefix,
            name=record['invoice_nbr'],
        )
        return {'name': name}

    @mapping
    def date_order(self, record):
        if record['submit_date']:
            return {'date_order': record['submit_date']}
        return {'date_order': record['add_date']}

    @mapping
    def partner_data(self, record):
        binder = self.binder_for('carepoint.carepoint.account')
        if record['acct_id']:
            account_unit = self.unit_for(
                CarepointAccountUnit, 'carepoint.carepoint.account',
            )
            accounts = account_unit._get_accounts(record['acct_id'])
            acct_id = binder.to_odoo(accounts[0], browse=True)
            patient_id = acct_id.patient_id
        else:
            patient_id = self.env.ref('connector_carepoint.patient_null')
        partner_id = patient_id.commercial_partner_id
        return {'partner_id': partner_id.id,
                'payment_term_id': partner_id.property_payment_term_id.id,
                }

    @mapping
    def pharmacy_id(self, record):
        binder = self.binder_for('carepoint.carepoint.store')
        store_id = binder.to_odoo(record['store_id'], browse=True)
        return {'pharmacy_id': store_id.pharmacy_id.id}

    @mapping
    # @only_create
    def state(self, record):

        # Close sale if older than close_sale_days
        if self.backend_record.close_sale_days:
            close_delta = timedelta(days=self.backend_record.close_sale_days)
            now = datetime.now()
            date = fields.Datetime.from_string(
                self.date_order(record)['date_order'],
            )
            if date + close_delta >= now:
                return {'state': 'done'}

        state_id = self.env.ref(
            'connector_carepoint.state_%d' % record['order_state_cn']
        )
        return {'state': state_id.order_state}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['order_id']}


@carepoint
class SaleOrderImporter(CarepointImporter,
                        CommonDateImporterMixer):
    _model_name = ['carepoint.sale.order']
    _base_mapper = SaleOrderImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        account_unit = self.unit_for(
            CarepointAccountUnit, 'carepoint.carepoint.account',
        )
        account_unit._import_account(record['acct_id'])

    def _after_import(self, binding):
        """ Import the sale lines & procurements """
        pass
        # line_unit = self.unit_for(
        #     SaleOrderLineUnit, model='carepoint.sale.order.line',
        # )
        # # @TODO: Eliminate circular import - sale.order.line depends on this,
        # #        which in turn imports sale lines.
        # line_unit._import_sale_order_lines(
        #     self.carepoint_id, binding.id,
        # )
        # proc_unit = self.unit_for(
        #     ProcurementOrderUnit, model='carepoint.procurement.order',
        # )
        # proc_unit._import_procurements_for_sale(
        #     self.carepoint_id,
        # )


@carepoint
class SaleOrderExportMapper(ExportMapper,
                            CommonDateExportMapperMixer):
    _model_name = 'carepoint.sale.order'

    direct = [
        ('date_order', 'submit_date'),
        (m2o_to_backend('carepoint_store_id',
                        binding='carepoint.carepoint.store'),
         'store_id'),
    ]

    @mapping
    @only_create
    def invoice_nbr(self, record):
        if not record.name:
            return
        return {
            'invoice_nbr': record.name.replace(
                self.backend_record.sale_prefix, '',
            )
        }

    @mapping
    @only_create
    def acct_id(self, record):
        binder = self.binder_for('carepoint.carepoint.account')
        conjoined = binder.to_backend(record.carepoint_account_id)
        _, acct_id = conjoined.split(',')
        return {'acct_id': acct_id}

    @mapping
    @only_create
    def static_defaults(self, record):
        return {'order_state_cn': 10,
                'order_status_cn': 1001,
                'hold_yn': 0,
                'priority_cn': 0,
                }


@carepoint
class SaleOrderExporter(CarepointExporter):
    _model_name = ['carepoint.sale.order']
    _base_mapper = SaleOrderExportMapper

    def _export_dependencies(self):
        self._export_dependency(
            self.binding_record.carepoint_account_id,
            'carepoint.carepoint.account',
        )
        self._export_dependency(
            self.binding_record.user_id,
            'carepoint.res.users',
        )
