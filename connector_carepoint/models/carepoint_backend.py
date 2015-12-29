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
from ..unit.import_synchronizer import (import_batch,
                                        DirectBatchImporter,
                                        CarepointImporter,
                                        )
from ..backend import carepoint
from ..connector import add_checkpoint

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
        default='CP/',
        help="A prefix put before the name of imported sales orders.\n"
             "For instance, if the prefix is 'cp-', the sales "
             "order 100000692 in Carepoint, will be named 'cp-100000692' "
             "in Odoo.",
    )
    store_ids = fields.One2many(
        comodel_name='carepoint.res.company',
        inverse_name='backend_id',
        string='Store',
        readonly=True,
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
    #
    # product_binding_ids = fields.One2many(
    #     comodel_name='carepoint.medical.medicament',
    #     inverse_name='backend_id',
    #     string='Carepoint Products',
    #     readonly=True,
    # )

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
            for model in ('carepoint.res.company',):
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
        # Records from Carepoint are imported based on their `add_date`
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
    #     self._import_from_date('carepoint.product.product',
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
    #     mag_product_obj = self.env['carepoint.product.product']
    #     domain = self._domain_for_update_product_stock_qty()
    #     carepoint_products = mag_product_obj.search(domain)
    #     carepoint_products.recompute_carepoint_qty()
    #     return True
    #
    # @api.model
    # def _carepoint_backend(self, callback, domain=None):
    #     if domain is None:
    #         domain = []
    #     backends = self.search(domain)
    #     if backends:
    #         getattr(backends, callback)()
    #
    # @api.model
    # def _scheduler_import_sale_orders(self, domain=None):
    #     self._carepoint_backend('import_sale_orders', domain=domain)
    #
    # @api.model
    # def _scheduler_import_customer_groups(self, domain=None):
    #     self._carepoint_backend('import_customer_groups', domain=domain)
    #
    # @api.model
    # def _scheduler_import_partners(self, domain=None):
    #     self._carepoint_backend('import_partners', domain=domain)
    #
    # @api.model
    # def _scheduler_import_product_categories(self, domain=None):
    #     self._carepoint_backend('import_product_categories', domain=domain)
    #
    # @api.model
    # def _scheduler_import_product_product(self, domain=None):
    #     self._carepoint_backend('import_product_product', domain=domain)
    #
    # @api.model
    # def _scheduler_update_product_stock_qty(self, domain=None):
    #     self._carepoint_backend('update_product_stock_qty', domain=domain)

    @api.multi
    def output_recorder(self):
        """ Utility method to output a file containing all the recorded
        requests / responses with Carepoint.  Used to generate test data.
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


@carepoint
class MetadataBatchImporter(DirectBatchImporter):
    """
    Import the records directly, without delaying the jobs.
    Import the Carepoint Stores
    They are imported directly because this is a rare and fast operation,
    and we don't really bother if it blocks the UI during this time.
    (that's also a mean to rapidly check the connectivity with Carepoint).
    """
    _model_name = [
        'carepoint.store',
    ]
