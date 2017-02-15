# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import pytz
from datetime import datetime, timedelta
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.base.res.res_partner import _tz_get
from ..unit.import_synchronizer import (import_batch,
                                        import_record,
                                        DirectBatchImporter,
                                        )
from ..backend import carepoint

_logger = logging.getLogger(__name__)

try:
    from carepoint.db import Db as CarepointDb
except ImportError:
    _logger.warning('Cannot import CarePoint')

IMPORT_DELTA_BUFFER = 30  # seconds


class CarepointBackend(models.Model):
    _name = 'carepoint.backend'
    _description = 'Carepoint Backend'
    _inherit = 'connector.backend'

    _backend_type = 'carepoint'

    _sql_constraints = [
        ('sale_prefix_uniq', 'unique(sale_prefix)',
         "A backend with the same sale prefix already exists"),
        ('rx_prefix_uniq', 'unique(rx_prefix)',
         "A backend with the same rx prefix already exists"),
    ]

    version = fields.Selection(
        selection='select_versions',
        required=True
    )
    db_driver = fields.Selection([
        (CarepointDb.ODBC_DRIVER, 'Production'),
        (CarepointDb.SQLITE, 'Testing'),
    ],
        default=CarepointDb.ODBC_DRIVER,
    )
    db_pool_size = fields.Integer(
        required=True,
        default=20,
        help='This is passed to SQLAlchemy `create_engine`',
    )
    db_max_overflow = fields.Integer(
        required=True,
        default=20,
        help='This is passed to SQLAlchemy `create_engine`',
    )
    db_pool_timeout = fields.Integer(
        required=True,
        default=30,
        help='This is passed to SQLAlchemy `create_engine`',
    )
    server = fields.Char(
        required=True,
        help="IP/DNS to Carepoint database",
    )
    username = fields.Char(
        string='Username',
        help="Database user",
        required=True,
    )
    password = fields.Char(
        string='Password',
        help="Database password",
        required=True,
    )
    sale_prefix = fields.Char(
        string='Sale Prefix',
        default='CSO/',
        help="A prefix put before the name of imported sales orders.\n"
             "For instance, if the prefix is 'cp-', the sales "
             "order 100000692 in Carepoint, will be named 'cp-100000692' "
             "in Odoo.",
    )
    rx_prefix = fields.Char(
        string='Rx Prefix',
        default='CRX/',
        help="A prefix put before the name of imported RX orders.\n"
             "For instance, if the prefix is 'cp-', the Rx "
             "order 100000692 in Carepoint, will be named 'cp-100000692' "
             "in Odoo.",
    )
    store_ids = fields.One2many(
        comodel_name='carepoint.carepoint.store',
        inverse_name='backend_id',
        string='Store',
        readonly=True,
    )
    server_tz = fields.Selection(
        _tz_get,
        'Server Time Zone',
        default=lambda s: s.env.user.tz,
        required=True,
    )
    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
        help="If a default language is selected, the records "
             "will be imported in the translation of this language.\n"
             "Note that a similar configuration exists "
             "for each storeview.",
    )
    default_tz = fields.Selection(
        _tz_get,
        'Default Time Zone',
        default=lambda s: s.env.user.tz,
        required=True,
    )
    default_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Default Product Category',
        help='If a default category is selected, products imported '
             'without a category will be linked to it.',
        required=True,
        default=lambda s: s.env.ref(
            'medical_prescription_sale.product_category_rx'),
    )
    default_account_payable_id = fields.Many2one(
        string='Default Account Payable',
        comodel_name='account.account',
        domain=lambda s: [('user_type_id.name', '=', 'Payable')],
        required=True,
    )
    default_account_receivable_id = fields.Many2one(
        string='Default Account Receivable',
        comodel_name='account.account',
        domain=lambda s: [('user_type_id.name', '=', 'Receivable')],
        required=True,
    )
    default_product_income_account_id = fields.Many2one(
        string='Default Product Income Account',
        comodel_name='account.account',
        domain=lambda s: [('user_type_id.name', '=', 'Income')],
        required=True,
    )
    default_product_expense_account_id = fields.Many2one(
        string='Default Product Expense Account',
        comodel_name='account.account',
        domain=lambda s: [('user_type_id.name', '=', 'Expenses')],
        required=True,
    )
    default_sale_tax = fields.Many2one(
        comodel_name='account.tax',
        domain="""[('type_tax_use', 'in', ('sale', 'none')),
                    ('company_id', '=', company_id)]""",
        required=True,
    )
    default_purchase_tax = fields.Many2one(
        comodel_name='account.tax',
        domain="""[('type_tax_use', 'in', ('purchase', 'none')),
                    ('company_id', '=', company_id)]""",
        required=True,
    )
    default_payment_journal = fields.Many2one(
        string='Default Payment Journal',
        comodel_name='account.journal',
        required=True,
    )
    default_customer_payment_term_id = fields.Many2one(
        string='Default Customer Payment Term',
        comodel_name='account.payment.term',
        required=True,
    )
    default_supplier_payment_term_id = fields.Many2one(
        string='Default Vendor Payment Term',
        comodel_name='account.payment.term',
        required=True,
    )
    import_items_from_date = fields.Datetime()
    import_patients_from_date = fields.Datetime()
    import_physicians_from_date = fields.Datetime()
    import_prescriptions_from_date = fields.Datetime()
    import_sales_from_date = fields.Datetime()
    import_addresses_from_date = fields.Datetime()
    import_phones_from_date = fields.Datetime()
    import_pickings_from_date = fields.Datetime()
    import_invoices_from_date = fields.Datetime()
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        default=lambda s: s.env.ref('base.main_company'),
    )
    is_default = fields.Boolean(
        default=True,
        help='Check this if this is the default connector for the company.'
        ' All newly created records for this company will be synced to the'
        ' default system. Only records that originated from non-default'
        ' systems will be synced with them.',
    )
    active = fields.Boolean(
        default=True,
    )
    #
    # product_binding_ids = fields.One2many(
    #     comodel_name='carepoint.medical.medicament',
    #     inverse_name='backend_id',
    #     string='Carepoint Products',
    #     readonly=True,
    # )

    @api.multi
    @api.constrains('is_default', 'company_id')
    def _check_default_for_company(self):
        for rec_id in self:
            domain = [
                ('company_id', '=', rec_id.company_id.id),
                ('is_default', '=', True),
            ]
            if len(self.search(domain)) > 1:
                raise ValidationError(_(
                    'This company already has a default CarePoint connector.',
                ))

    @api.model
    def __get_model_session(self):
        return ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context
        )

    @api.model
    def select_versions(self):
        """ Available versions in the backend.
        Can be inherited to add custom versions.  Using this method
        to add a version from an ``_inherit`` does not constrain
        to redefine the ``version`` field in the ``_inherit`` model.
        """
        return [('2.99', '2.99+')]

    @api.multi
    def check_carepoint_structure(self):
        """ Used in each data import """
        self.synchronize_metadata()
        return True

    @api.multi
    def synchronize_metadata(self):
        session = self.__get_model_session()
        for backend in self:
            for model in ('carepoint.carepoint.store',
                          # 'carepoint.res.users',
                          ):
                # import directly, do not delay because this
                # is a fast operation, a direct return is fine
                # and it is simpler to import them sequentially
                import_batch(session, model, backend.id)
        return True

    @api.multi
    def _import_all(self, model):
        session = self.__get_model_session()
        for backend in self:
            backend.check_carepoint_structure()
            import_batch.delay(session, model, backend.id)

    @api.multi
    def _import_from_date(self, model, from_date_field,
                          chg_date_field='chg_date'):
        session = self.__get_model_session()
        utc_now = pytz.timezone('UTC').localize(datetime.utcnow())
        for backend in self:
            local_tz = pytz.timezone(backend.server_tz)
            import_start_time = utc_now.astimezone(local_tz).replace(
                tzinfo=None
            )
            backend.check_carepoint_structure()
            filters = {chg_date_field: {'<=': import_start_time}}
            from_date = getattr(backend, from_date_field)
            if from_date:
                filters[chg_date_field]['>='] = fields.Datetime.from_string(
                    from_date
                )
            else:
                from_date = None
            import_batch.delay(session, model, backend.id, filters=filters)
            # Records from Carepoint are imported based on their `add_date`
            # date.  This date is set on Carepoint at the beginning of a
            # transaction, so if the import is run between the beginning and
            # the end of a transaction, the import of a record may be
            # missed.  That's why we add a small buffer back in time where
            # the eventually missed records will be retrieved.  This also
            # means that we'll have jobs that import twice the same records,
            # but this is not a big deal because they will be skipped when
            # the last `sync_date` is the same.
            next_time = (import_start_time -
                         timedelta(seconds=IMPORT_DELTA_BUFFER))
            next_time = fields.Datetime.to_string(next_time)
            backend.write({from_date_field: next_time})

    @api.model
    def resync_all(self, binding_model):
        """ Resync all bindings for model """
        session = self.__get_model_session()
        for record_id in self.env[binding_model].search([]):
            for binding_id in record_id.carepoint_bind_ids:
                import_record.delay(session,
                                    binding_model,
                                    binding_id.backend_id.id,
                                    binding_id.carepoint_id,
                                    force=True,
                                    )

    @api.model
    def force_sync(self, binding_model, remote_pk, backend_id):
        """ Force sycronization based on model and primary key """
        session = self.__get_model_session()
        import_record.delay(session,
                            binding_model,
                            backend_id,
                            remote_pk,
                            force=True,
                            )

    @api.multi
    def import_carepoint_item(self):
        self._import_from_date('carepoint.carepoint.item',
                               'import_items_from_date')
        return True

    @api.multi
    def import_medical_patient(self):
        self._import_from_date('carepoint.medical.patient',
                               'import_patients_from_date')
        return True

    @api.model
    def cron_import_medical_patient(self):
        self.search([]).import_medical_patient()

    @api.multi
    def import_medical_physician(self):
        self._import_from_date('carepoint.medical.physician',
                               'import_physicians_from_date')
        return True

    @api.model
    def cron_import_medical_physician(self):
        self.search([]).import_medical_physician()

    @api.multi
    def import_medical_prescription(self):
        self._import_from_date('carepoint.rx.ord.ln',
                               'import_prescriptions_from_date')
        return True

    @api.model
    def cron_import_medical_prescription(self):
        self.search([]).import_medical_prescription()

    @api.multi
    def import_sale_order(self):
        self._import_from_date('carepoint.sale.order.line',
                               'import_sales_from_date')

    @api.model
    def cron_import_sale_order(self):
        self.search([]).import_sale_order()

    @api.multi
    def import_stock_picking(self):
        self._import_from_date('carepoint.stock.picking',
                               'import_pickings_from_date')

    @api.multi
    def import_account_invoice(self):
        self._import_from_date('carepoint.account.invoice.line',
                               'import_invoices_from_date',
                               'primary_pay_date')

    @api.multi
    def import_address(self):
        self._import_from_date('carepoint.carepoint.address',
                               'import_addresses_from_date')

    @api.model
    def cron_import_address(self):
        self.search([]).import_address()

    @api.multi
    def import_phone(self):
        self._import_from_date('carepoint.carepoint.phone',
                               'import_phones_from_date')

    @api.model
    def cron_import_phone(self):
        self.search([]).import_phone()

    @api.multi
    def import_fdb(self):
        # self._import_all('carepoint.fdb.img.mfg')
        # self._import_all('carepoint.fdb.img.date')
        # self._import_all('carepoint.fdb.img.id')
        # self._import_all('carepoint.fdb.img')
        self._import_all('carepoint.fdb.route')
        self._import_all('carepoint.fdb.form')
        self._import_all('carepoint.fdb.unit')
        # self._import_all('carepoint.fdb.gcn')
        # self._import_all('carepoint.fdb.lbl.rid')
        # self._import_all('carepoint.fdb.ndc')
        # self._import_all('carepoint.fdb.gcn.seq')
        return True


@carepoint
class MetadataBatchImporter(DirectBatchImporter):
    """ Import the records directly, without delaying the jobs.
    Import the Carepoint Stores
    They are imported directly because this is a rare and fast operation,
    and we don't really bother if it blocks the UI during this time.
    (that's also a mean to rapidly check the connectivity with Carepoint).
    """
    _model_name = [
        'carepoint.store',
    ]
