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


@carepoint
class AccountInvoiceLineAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Patient """
    _model_name = 'carepoint.account.invoice.line'


@carepoint
class AccountInvoiceLineBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Patients.
    For every order in the list, a delayed job is created.
    """
    _model_name = ['carepoint.account.invoice.line']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class AccountInvoiceLineImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.account.invoice.line'

    direct = [
        # ('submit_date', 'date_order'),
    ]

    # @mapping
    # @only_create
    # def state(self, record):
    #     state_id = self.env.ref(
    #         'connector_carepoint.state_%d' % record['order_state_cn']
    #     )
    #     return {'state': state_id.order_state}

    @mapping
    @only_create
    def invoice_id(self, record):
        binder = self.binder_for('carepoint.procurement.order')
        proc_id = binder.to_odoo(record['rxdisp_id'])
        proc_id = self.env['procurement.order'].browse(proc_id)
        invoice_id = proc_id.sale_line_id.order_id.invoice_ids
        if len(invoice_id):
            invoice_id = invoice_id[0]
        else:
            invoice_id = self.env['account.invoice'].create(
                proc_id.sale_line_id.order_id._prepare_invoice()
            )
        return {'invoice_id': invoice_id.id}

    @mapping
    def invoice_lines(self, record):
        binder = self.binder_for('carepoint.procurement.order')
        proc_id = binder.to_odoo(record['rxdisp_id'])
        proc_id = self.env['procurement.order'].browse(proc_id)
        line_id = proc_id.sale_line_id
        qty = line_id.product_uom_qty
        line_id.price_unit = record['t_patient_pay_paid'] / qty
        return line_id._prepare_invoice_line(qty)

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['rxdisp_id']}


@carepoint
class AccountInvoiceLineImporter(CarepointImporter):
    _model_name = ['carepoint.account.invoice.line']

    _base_mapper = AccountInvoiceLineImportMapper

    def _create(self, data):
        binding = super(AccountInvoiceLineImporter, self)._create(data)
        checkpoint = self.unit_for(AccountInvoiceLineAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['rxdisp_id'],
                                'carepoint.procurement.order')

    #
    # def _after_import(self, partner_binding):
    #     """ Import the addresses """
    #     book = self.unit_for(PartnerAddressBook, model='carepoint.address')
    #     book.import_addresses(self.carepoint_id, partner_binding.id)


@carepoint
class AccountInvoiceLineExportMapper(ExportMapper):
    _model_name = 'carepoint.account.invoice.line'

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
class AccountInvoiceLineExporter(CarepointExporter):
    _model_name = ['carepoint.account.invoice.line']
    _base_mapper = AccountInvoiceLineExportMapper


@carepoint
class AccountInvoiceLineDeleteSynchronizer(CarepointDeleter):
    _model_name = ['carepoint.account.invoice.line']


@carepoint
class AccountInvoiceLineAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.account.invoice.line record """
    _model_name = ['carepoint.account.invoice.line', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)
