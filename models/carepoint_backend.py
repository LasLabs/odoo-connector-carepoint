# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Dave Lasley <dave@laslabs.com>
#    Copyright: 2015 LasLabs, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from datetime import datetime, timedelta
from openerp import models, fields, api, _
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import mapping, ImportMapper
from .unit.backend_adapter import GenericAdapter
from .unit.import_synchronizer import (import_batch,
                                       DirectBatchImporter,
                                       CarepointImporter,
                                       )
from .partner import partner_import_batch
from .sale import sale_order_import_batch
from .backend import carepoint
from .connector import add_checkpoint

_logger = logging.getLogger(__name__)

IMPORT_DELTA_BUFFER = 30  # seconds


class CarepointBackend(models.Model):
    _name = 'carepoint.backend'
    _description = 'Carepoint Backend'
    _inherit = 'connector.backend'

    _backend_type = 'carepoint'

    @api.model
    def select_versions(self):
        """ Available versions in the backend.
        Can be inherited to add custom versions.  Using this method
        to add a version from an ``_inherit`` does not constrain
        to redefine the ``version`` field in the ``_inherit`` model.
        """
        return [('2.99', '2.99+')]
    
    version = fields.Selection(
        selection='select_versions',
        required=True
    )
    server = fields.Char(
        required=True,
        help="IP/DNS to Carepoint database",
    )
    username = fields.Char(
        string='Username',
        help="Database user",
    )
    password = fields.Char(
        string='Password',
        help="Database password",
    )
    sale_prefix = fields.Char(
        string='Sale Prefix',
        default='cp-',
        help="A prefix put before the name of imported sales orders.\n"
             "For instance, if the prefix is 'cp-', the sales "
             "order 100000692 in Carepoint, will be named 'cp-100000692' "
             "in Odoo.",
    )
    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
        help="If a default language is selected, the records "
             "will be imported in the translation of this language.\n"
             "Note that a similar configuration exists "
             "for each storeview.",
    )
    default_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Default Product Category',
        help='If a default category is selected, products imported '
             'without a category will be linked to it.',
    )

    product_binding_ids = fields.One2many(
        comodel_name='carepoint.medical.medicament',
        inverse_name='backend_id',
        string='Carepoint Products',
        readonly=True,
    )

    _sql_constraints = [
        ('sale_prefix_uniq', 'unique(sale_prefix)',
         "A backend with the same sale prefix already exists")
    ]

    @api.multi
    def check_carepoint_structure(self):
        """ Used in each data import.
        Verify if a store exists for each backend before starting the import.
        """
        for backend in self:
            stores = backend.stores
            if not stores:
                backend.synchronize_metadata()
        return True

    @api.multi
    def synchronize_metadata(self):
        session = ConnectorSession()
        for backend in self:
            for model in ('carepoint.store',):
                # import directly, do not delay because this
                # is a fast operation, a direct return is fine
                # and it is simpler to import them sequentially
                import_batch(session, model, backend.id)
        return True

    @api.multi
    def _import_from_date(self, model, from_date_field):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        import_start_time = datetime.now()
        for backend in self:
            backend.check_carepoint_structure()
            from_date = getattr(backend, from_date_field)
            if from_date:
                from_date = fields.Datetime.from_string(from_date)
            else:
                from_date = None
            import_batch.delay(session, model,
                               backend.id,
                               filters={'from_date': from_date,
                                        'to_date': import_start_time})
        # Records from Carepoint are imported based on their `created_at`
        # date.  This date is set on Carepoint at the beginning of a
        # transaction, so if the import is run between the beginning and
        # the end of a transaction, the import of a record may be
        # missed.  That's why we add a small buffer back in time where
        # the eventually missed records will be retrieved.  This also
        # means that we'll have jobs that import twice the same records,
        # but this is not a big deal because they will be skipped when
        # the last `sync_date` is the same.
        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({from_date_field: next_time})
    # 
    # @api.multi
    # def import_partners(self):
    #     """ Import partners from all store """
    #     for backend in self:
    #         backend.check_carepoint_structure()
    #         backend.store_ids.import_partners()
    #     return True
    # 
    # @api.multi
    # def import_prescription_order(self):
    #     """ Import prescription orders from associated stores """
    #     store_obj = self.env['carepoint.store']
    #     stores = store_obj.search([('backend_id', 'in', self.ids)])
    #     stores.import_prescription_orders()
    #     return True
    # 
    # @api.multi
    # def import_medical_medicament(self):
    #     self._import_from_date('magento.product.product',
    #                            'import_products_from_date')
    #     return True
    # 
    # @api.multi
    # def _domain_for_update_product_stock_qty(self):
    #     return [
    #         ('backend_id', 'in', self.ids),
    #         ('type', '!=', 'service'),
    #         ('no_stock_sync', '=', False),
    #     ]
    # 
    # @api.multi
    # def update_product_stock_qty(self):
    #     mag_product_obj = self.env['magento.product.product']
    #     domain = self._domain_for_update_product_stock_qty()
    #     magento_products = mag_product_obj.search(domain)
    #     magento_products.recompute_magento_qty()
    #     return True
    # 
    # @api.model
    # def _magento_backend(self, callback, domain=None):
    #     if domain is None:
    #         domain = []
    #     backends = self.search(domain)
    #     if backends:
    #         getattr(backends, callback)()
    # 
    # @api.model
    # def _scheduler_import_sale_orders(self, domain=None):
    #     self._magento_backend('import_sale_orders', domain=domain)
    # 
    # @api.model
    # def _scheduler_import_customer_groups(self, domain=None):
    #     self._magento_backend('import_customer_groups', domain=domain)
    # 
    # @api.model
    # def _scheduler_import_partners(self, domain=None):
    #     self._magento_backend('import_partners', domain=domain)
    # 
    # @api.model
    # def _scheduler_import_product_categories(self, domain=None):
    #     self._magento_backend('import_product_categories', domain=domain)
    # 
    # @api.model
    # def _scheduler_import_product_product(self, domain=None):
    #     self._magento_backend('import_product_product', domain=domain)
    # 
    # @api.model
    # def _scheduler_update_product_stock_qty(self, domain=None):
    #     self._magento_backend('update_product_stock_qty', domain=domain)

    @api.multi
    def output_recorder(self):
        """ Utility method to output a file containing all the recorded
        requests / responses with Magento.  Used to generate test data.
        Should be called with ``erppeek`` for instance.
        """
        from .unit.backend_adapter import output_recorder
        import os
        import tempfile
        fmt = '%Y-%m-%d-%H-%M-%S'
        timestamp = datetime.now().strftime(fmt)
        filename = 'output_%s_%s' % (self.env.cr.dbname, timestamp)
        path = os.path.join(tempfile.gettempdir(), filename)
        output_recorder(path)
        return path


class MagentoWebsite(models.Model):
    _name = 'magento.website'
    _inherit = 'magento.binding'
    _description = 'Magento Website'

    _order = 'sort_order ASC, id ASC'

    name = fields.Char(required=True, readonly=True)
    code = fields.Char(readonly=True)
    sort_order = fields.Integer(string='Sort Order', readonly=True)
    store_ids = fields.One2many(
        comodel_name='magento.store',
        inverse_name='website_id',
        string='Stores',
        readonly=True,
    )
    import_partners_from_date = fields.Datetime(
        string='Import partners from date',
    )
    product_binding_ids = fields.Many2many(
        comodel_name='magento.product.product',
        string='Magento Products',
        readonly=True,
    )

    @api.multi
    def import_partners(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        import_start_time = datetime.now()
        for website in self:
            backend_id = website.backend_id.id
            if website.import_partners_from_date:
                from_string = fields.Datetime.from_string
                from_date = from_string(website.import_partners_from_date)
            else:
                from_date = None
            partner_import_batch.delay(
                session, 'magento.res.partner', backend_id,
                {'magento_website_id': website.magento_id,
                 'from_date': from_date,
                 'to_date': import_start_time})
        # Records from Magento are imported based on their `created_at`
        # date.  This date is set on Magento at the beginning of a
        # transaction, so if the import is run between the beginning and
        # the end of a transaction, the import of a record may be
        # missed.  That's why we add a small buffer back in time where
        # the eventually missed records will be retrieved.  This also
        # means that we'll have jobs that import twice the same records,
        # but this is not a big deal because they will be skipped when
        # the last `sync_date` is the same.
        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({'import_partners_from_date': next_time})
        return True


class MagentoStore(models.Model):
    _name = 'magento.store'
    _inherit = 'magento.binding'
    _description = 'Magento Store'

    name = fields.Char()
    website_id = fields.Many2one(
        comodel_name='magento.website',
        string='Magento Website',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    backend_id = fields.Many2one(
        comodel_name='magento.backend',
        related='website_id.backend_id',
        string='Magento Backend',
        store=True,
        readonly=True,
        # override 'magento.binding', can't be INSERTed if True:
        required=False,
    )
    storeview_ids = fields.One2many(
        comodel_name='magento.storeview',
        inverse_name='store_id',
        string="Storeviews",
        readonly=True,
    )
    send_picking_done_mail = fields.Boolean(
        string='Send email notification on picking done',
        help="Does the picking export/creation should send "
             "an email notification on Magento side?",
    )
    send_invoice_paid_mail = fields.Boolean(
        string='Send email notification on invoice validated/paid',
        help="Does the invoice export/creation should send "
             "an email notification on Magento side?",
    )
    create_invoice_on = fields.Selection(
        selection=[('open', 'Validate'),
                   ('paid', 'Paid')],
        string='Create invoice on action',
        default='paid',
        required=True,
        help="Should the invoice be created in Magento "
             "when it is validated or when it is paid in Odoo?\n"
             "This only takes effect if the sales order's related "
             "payment method is not giving an option for this by "
             "itself. (See Payment Methods)",
    )


class MagentoStoreview(models.Model):
    _name = 'magento.storeview'
    _inherit = 'magento.binding'
    _description = "Magento Storeview"

    _order = 'sort_order ASC, id ASC'

    name = fields.Char(required=True, readonly=True)
    code = fields.Char(readonly=True)
    enabled = fields.Boolean(string='Enabled', readonly=True)
    sort_order = fields.Integer(string='Sort Order', readonly=True)
    store_id = fields.Many2one(comodel_name='magento.store',
                               string='Store',
                               ondelete='cascade',
                               readonly=True)
    lang_id = fields.Many2one(comodel_name='res.lang', string='Language')
    section_id = fields.Many2one(comodel_name='crm.case.section',
                                 string='Sales Team')
    backend_id = fields.Many2one(
        comodel_name='magento.backend',
        related='store_id.website_id.backend_id',
        string='Magento Backend',
        store=True,
        readonly=True,
        # override 'magento.binding', can't be INSERTed if True:
        required=False,
    )
    import_orders_from_date = fields.Datetime(
        string='Import sale orders from date',
        help='do not consider non-imported sale orders before this date. '
             'Leave empty to import all sale orders',
    )
    no_sales_order_sync = fields.Boolean(
        string='No Sales Order Synchronization',
        help='Check if the storeview is active in Magento '
             'but its sales orders should not be imported.',
    )
    catalog_price_tax_included = fields.Boolean(string='Prices include tax')

    @api.multi
    def import_sale_orders(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        import_start_time = datetime.now()
        for storeview in self:
            if storeview.no_sales_order_sync:
                _logger.debug("The storeview '%s' is active in Magento "
                              "but is configured not to import the "
                              "sales orders", storeview.name)
                continue
            backend_id = storeview.backend_id.id
            if storeview.import_orders_from_date:
                from_string = fields.Datetime.from_string
                from_date = from_string(storeview.import_orders_from_date)
            else:
                from_date = None
            sale_order_import_batch.delay(
                session,
                'magento.sale.order',
                backend_id,
                {'magento_storeview_id': storeview.magento_id,
                 'from_date': from_date,
                 'to_date': import_start_time},
                priority=1)  # executed as soon as possible
        # Records from Magento are imported based on their `created_at`
        # date.  This date is set on Magento at the beginning of a
        # transaction, so if the import is run between the beginning and
        # the end of a transaction, the import of a record may be
        # missed.  That's why we add a small buffer back in time where
        # the eventually missed records will be retrieved.  This also
        # means that we'll have jobs that import twice the same records,
        # but this is not a big deal because the sales orders will be
        # imported the first time and the jobs will be skipped on the
        # subsequent imports
        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({'import_orders_from_date': next_time})
        return True


@magento
class WebsiteAdapter(GenericAdapter):
    _model_name = 'magento.website'
    _magento_model = 'ol_websites'
    _admin_path = 'system_store/editWebsite/website_id/{id}'


@magento
class StoreAdapter(GenericAdapter):
    _model_name = 'magento.store'
    _magento_model = 'ol_groups'
    _admin_path = 'system_store/editGroup/group_id/{id}'


@magento
class StoreviewAdapter(GenericAdapter):
    _model_name = 'magento.storeview'
    _magento_model = 'ol_storeviews'
    _admin_path = 'system_store/editStore/store_id/{id}'


@magento
class MetadataBatchImporter(DirectBatchImporter):
    """ Import the records directly, without delaying the jobs.
    Import the Magento Websites, Stores, Storeviews
    They are imported directly because this is a rare and fast operation,
    and we don't really bother if it blocks the UI during this time.
    (that's also a mean to rapidly check the connectivity with Magento).
    """
    _model_name = [
        'magento.website',
        'magento.store',
        'magento.storeview',
    ]


MetadataBatchImport = MetadataBatchImporter  # deprecated


@magento
class WebsiteImportMapper(ImportMapper):
    _model_name = 'magento.website'

    direct = [('code', 'code'),
              ('sort_order', 'sort_order')]

    @mapping
    def name(self, record):
        name = record['name']
        if name is None:
            name = _('Undefined')
        return {'name': name}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@magento
class StoreImportMapper(ImportMapper):
    _model_name = 'magento.store'

    direct = [('name', 'name')]

    @mapping
    def website_id(self, record):
        binder = self.binder_for(model='magento.website')
        binding_id = binder.to_odoo(record['website_id'])
        return {'website_id': binding_id}


@magento
class StoreviewImportMapper(ImportMapper):
    _model_name = 'magento.storeview'

    direct = [
        ('name', 'name'),
        ('code', 'code'),
        ('is_active', 'enabled'),
        ('sort_order', 'sort_order'),
    ]

    @mapping
    def store_id(self, record):
        binder = self.binder_for(model='magento.store')
        binding_id = binder.to_odoo(record['group_id'])
        return {'store_id': binding_id}


@magento
class StoreImporter(MagentoImporter):
    """ Import one Magento Store (create a sale.shop via _inherits) """
    _model_name = ['magento.store',
                   ]

    def _create(self, data):
        binding = super(StoreImporter, self)._create(data)
        checkpoint = self.unit_for(StoreAddCheckpoint)
        checkpoint.run(binding.id)
        return binding


StoreImport = StoreImporter  # deprecated


@magento
class StoreviewImporter(MagentoImporter):
    """ Import one Magento Storeview """
    _model_name = ['magento.storeview',
                   ]

    def _create(self, data):
        binding = super(StoreviewImporter, self)._create(data)
        checkpoint = self.unit_for(StoreAddCheckpoint)
        checkpoint.run(binding.id)
        return binding


StoreviewImport = StoreviewImporter  # deprecated


@magento
class StoreAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the magento.storeview
    or magento.store record
    """
    _model_name = ['magento.storeview',
                   'magento.store',
                   ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)

# backward compatibility
StoreViewAddCheckpoint = magento(StoreAddCheckpoint)
