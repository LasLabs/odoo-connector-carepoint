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
from collections import defaultdict
from openerp import models, fields, api
# from openerp.addons.connector.queue.job import job, related_action
# from openerp.addons.connector.event import on_record_write
# from openerp.addons.connector.unit.synchronizer import (Importer,
#                                                         Exporter,
#                                                         )

from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        # TranslationImporter,
                                        AddCheckpoint,
                                        )
# from ..connector import get_environment
from ..backend import carepoint
# from ..related_action import unwrap_binding

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in xrange(0, len(items), length):
        yield items[index:index + length]


class CarepointMedicalMedicament(models.Model):
    _name = 'carepoint.medical.medicament'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.medicament': 'odoo_id'}
    _description = 'Carepoint Medicament'

    odoo_id = fields.Many2one(
        string='Medicament',
        comodel_name='medical.medicament',
        required=True,
        ondelete='restrict'
    )
    store_ids = fields.Many2many(
        string='Stores',
        comodel_name='carepoint.res.company',
        readonly=True
    )
    created_at = fields.Date('Created At (on Carepoint)')
    updated_at = fields.Date('Updated At (on Carepoint)')
    manage_stock = fields.Selection(
        selection=[('use_default', 'Use Default Config'),
                   ('no', 'Do Not Manage Stock'),
                   ('yes', 'Manage Stock')],
        string='Manage Stock Level',
        default='use_default',
        required=True,
    )
    backorders = fields.Selection(
        selection=[('use_default', 'Use Default Config'),
                   ('no', 'No Sell'),
                   ('yes', 'Sell Quantity < 0'),
                   ('yes-and-notification', 'Sell Quantity < 0 and '
                                            'Use Customer Notification')],
        string='Manage Inventory Backorders',
        default='use_default',
        required=True,
    )
    carepoint_qty = fields.Float(
        string='Computed Quantity',
        help="Last computed quantity to send on Carepoint."
    )
    no_stock_sync = fields.Boolean(
        string='No Stock Synchronization',
        required=False,
        help="Check this to exclude the product "
             "from stock synchronizations.",
    )

    RECOMPUTE_QTY_STEP = 1000  # products at a time

    @api.multi
    def recompute_carepoint_qty(self):
        """ Check if the quantity in the stock location configured
        on the backend has changed since the last export.
        If it has changed, write the updated quantity on `carepoint_qty`.
        The write on `carepoint_qty` will trigger an `on_record_write`
        event that will create an export job.
        It groups the products by backend to avoid to read the backend
        informations for each product.
        """
        # group products by backend
        backends = defaultdict(self.browse)
        for product in self:
            backends[product.backend_id] |= product

        for backend, products in backends.iteritems():
            self._recompute_carepoint_qty_backend(backend, products)
        return True

    @api.multi
    def _recompute_carepoint_qty_backend(self, backend, products,
                                         read_fields=None):
        """ Recompute the products quantity for one backend.
        If field names are passed in ``read_fields`` (as a list), they
        will be read in the product that is used in
        :meth:`~._carepoint_qty`.
        """
        if backend.product_stock_field_id:
            stock_field = backend.product_stock_field_id.name
        else:
            stock_field = 'virtual_available'

        location = backend.warehouse_id.lot_stock_id

        product_fields = ['carepoint_qty', stock_field]
        if read_fields:
            product_fields += read_fields

        self_with_location = self.with_context(location=location.id)
        for chunk_ids in chunks(products.ids, self.RECOMPUTE_QTY_STEP):
            records = self_with_location.browse(chunk_ids)
            for product in records.read(fields=product_fields):
                new_qty = self._carepoint_qty(
                    product, backend, location, stock_field
                )
                if new_qty != product['carepoint_qty']:
                    self.browse(product['id']).carepoint_qty = new_qty

    @api.multi
    def _carepoint_qty(self, product, backend, location, stock_field):
        """ Return the current quantity for one product.
        Can be inherited to change the way the quantity is computed,
        according to a backend / location.
        If you need to read additional fields on the product, see the
        ``read_fields`` argument of :meth:`~._recompute_carepoint_qty_backend`
        """
        return product[stock_field]


class MedicalMedicament(models.Model):
    _inherit = 'medical.medicament'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.medicament',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class MedicalMedicamentAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.medical.medicament'
    _cp_lib = 'item'  # Name of model in Carepoint lib (snake_case)

    def search(self, filters=None, from_date=None, to_date=None):
        """ Search records according to some criteria and return results
        :param filters: Filters to apply to search
        :type filters: dict or None
        :rtype: :class:`sqlalchemy.engine.ResultProxy`
        """
        if filters is None:
            filters = {}
        if from_date is not None:
            filters.setdefault('updated_at', {})
            filters['updated_at']['<='] = from_date
        if to_date is not None:
            filters.setdefault('updated_at', {})
            filters['updated_at']['>='] = to_date
        return super(MedicalMedicamentAdapter, self).search(filters)

    # def get_images(self, id, storeview_id=None):
    #     return self._call('product_media.list',
    #                       [int(id), storeview_id, 'id'])
    #
    # def read_image(self, id, image_name, storeview_id=None):
    #     return self._call('product_media.info',
    #                       [int(id), image_name, storeview_id, 'id'])
    #
    # def update_inventory(self, id, data):
    #     # product_stock.update is too slow
    #     return self._call('oerp_cataloginventory_stock_item.update',
    #                       [int(id), data])


@carepoint
class MedicamentBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Medicaments.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.medical.medicament']

    def run(self, filters=None):
        """ Run the synchronization """
        from_date = filters.pop('from_date', None)
        to_date = filters.pop('to_date', None)
        record_ids = self.backend_adapter.search(
            filters, from_date=from_date, to_date=to_date
        )
        _logger.info('Search for carepoint products %s returned %s',
                     filters, record_ids)
        for record_id in record_ids:
            self._import_record(record_id)

#
# @carepoint
# class CatalogImageImporter(Importer):
#     """ Import images for a record.
#     Usually called from importers, in ``_after_import``.
#     For instance from the products importer.
#     """
#
#     _model_name = ['carepoint.medical.medicament',
#                    ]
#
#     def _get_images(self, storeview_id=None):
#         return self.backend_adapter.get_images(
#             self.carepoint_id, storeview_id)
#
#     def _sort_images(self, images):
#         """ Returns a list of images sorted by their priority.
#         An image with the 'image' type is the the primary one.
#         The other images are sorted by their position.
#         The returned list is reversed, the items at the end
#         of the list have the higher priority.
#         """
#         if not images:
#             return {}
#         # place the images where the type is 'image' first then
#         # sort them by the reverse priority (last item of the list has
#         # the the higher priority)
#
#         def priority(image):
#             primary = 'image' in image['types']
#             try:
#                 position = int(image['position'])
#             except ValueError:
#                 position = sys.maxint
#             return (primary, -position)
#         return sorted(images, key=priority)
#
#     def _get_binary_image(self, image_data):
#         url = image_data['url'].encode('utf8')
#         try:
#             request = urllib2.Request(url)
#             if self.backend_record.auth_basic_username \
#                     and self.backend_record.auth_basic_password:
#                 base64string = base64.encodestring(
#                     '%s:%s' % (self.backend_record.auth_basic_username,
#                                self.backend_record.auth_basic_password))
#                 request.add_header(
#                     "Authorization", "Basic %s" % base64string)
#             binary = urllib2.urlopen(request)
#         except urllib2.HTTPError as err:
#             if err.code == 404:
#                 # the image is just missing, we skip it
#                 return
#             else:
#                 # we don't know why we couldn't download the image
#                 # so we propagate the error, the import will fail
#                 # and we have to check why it couldn't be accessed
#                 raise
#         else:
#             return binary.read()
#
#     def run(self, carepoint_id, binding_id):
#         self.carepoint_id = carepoint_id
#         images = self._get_images()
#         images = self._sort_images(images)
#         binary = None
#         while not binary and images:
#             binary = self._get_binary_image(images.pop())
#         if not binary:
#             return
#         model = self.model.with_context(connector_no_export=True)
#         binding = model.browse(binding_id)
#         binding.write({'image': base64.b64encode(binary)})


@carepoint
class MedicamentImportMapper(ImportMapper):
    _model_name = 'carepoint.medical.medicament'
    direct = [
        ('name', 'DESC'),
        ('description', 'DESC'),
        ('sku', 'SKU'),
        ('ean13', 'UPCCODE'),
        ('ndc', 'NDC'),
        ('company_id', 'store_id'),
        ('short_description', 'DESC'),
        ('created_at', 'add_date'),
        ('updated_at', 'chg_date'),
    ]

    @mapping
    def is_active(self, record):
        mapper = self.unit_for(IsActiveMedicamentImportMapper)
        return mapper.map_record(record).values(**self.options)

    @mapping
    def price(self, record):
        mapper = self.unit_for(PriceMedicamentImportMapper)
        return mapper.map_record(record).values(**self.options)

    @mapping
    def store_ids(self, record):
        # @TODO: somehow combine the products for stores
        return {'store_ids': [record['store_id']]}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['item_id']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@carepoint
class MedicamentImporter(CarepointImporter):
    _model_name = ['carepoint.medical.medicament']

    _base_mapper = MedicamentImportMapper

    def _import_bundle_dependencies(self):
        """ Import the dependencies for a Bundle """
        bundle = self.carepoint_record['_bundle_data']
        for option in bundle['options']:
            for selection in option['selections']:
                self._import_dependency(selection['item_id'],
                                        'carepoint.medical.medicament')

    def _import_dependencies(self):
        """ Import the dependencies for the record """
        record = self.carepoint_record
        if record['type_id'] == 'bundle':
            self._import_bundle_dependencies()

    def _must_skip(self):
        """ Hook called right after we read the data from the backend.
        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).
        If it returns None, the import will continue normally.
        :returns: None | str | unicode
        """
        pass

    def _validate_data(self, data):
        """ Check if the values to import are correct
        Pro-actively check before the ``_create`` or
        ``_update`` if some fields are missing or invalid
        Raise `InvalidDataError`
        """
        pass

    def _create(self, data):
        odoo_binding = super(MedicamentImporter, self)._create(data)
        checkpoint = self.unit_for(AddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        pass
        # translation_importer = self.unit_for(TranslationImporter)
        # translation_importer.run(self.carepoint_id, binding.id,
        #                          mapper_class=MedicamentImportMapper)
        # image_importer = self.unit_for(CatalogImageImporter)
        # image_importer.run(self.carepoint_id, binding.id)


@carepoint
class PriceMedicamentImportMapper(ImportMapper):
    _model_name = 'carepoint.medical.medicament'

    @mapping
    def price(self, record):
        return {'list_price': record.get('COST', 0.0)}


@carepoint
class IsActiveMedicamentImportMapper(ImportMapper):
    _model_name = 'carepoint.medical.medicament'

    @mapping
    def is_active(self, record):
        """Check if the product is active in Carepoint
        and set active flag in OpenERP
        status == 1 in Carepoint means active"""
        return {'active': (record.get('ACTIVE_YN') == 1)}


# @carepoint
# class MedicamentInventoryExporter(Exporter):
#     _model_name = ['carepoint.medical.medicament']
#
#     _map_backorders = {'use_default': 0,
#                        'no': 0,
#                        'yes': 1,
#                        'yes-and-notification': 2,
#                        }
#
#     def _get_data(self, product, fields):
#         result = {}
#         if 'carepoint_qty' in fields:
#             result.update({
#                 'qty': product.carepoint_qty,
#                 # put the stock availability to "out of stock"
#                 'is_in_stock': int(product.carepoint_qty > 0)
#             })
#         if 'manage_stock' in fields:
#             manage = product.manage_stock
#             result.update({
#                 'manage_stock': int(manage == 'yes'),
#                 'use_config_manage_stock': int(manage == 'use_default'),
#             })
#         if 'backorders' in fields:
#             backorders = product.backorders
#             result.update({
#                 'backorders': self._map_backorders[backorders],
#                 'use_config_backorders': int(backorders == 'use_default'),
#             })
#         return result
#
#     def run(self, binding_id, fields):
#         """ Export the product inventory to Carepoint """
#         product = self.model.browse(binding_id)
#         carepoint_id = self.binder.to_backend(product.id)
#         data = self._get_data(product, fields)
#         self.backend_adapter.update_inventory(carepoint_id, data)
#
#
# # fields which should not trigger an export of the products
# # but an export of their inventory
# INVENTORY_FIELDS = ('manage_stock',
#                     'backorders',
#                     'carepoint_qty',
#                     )
#
#
# @on_record_write(model_names='carepoint.medical.medicament')
# def carepoint_product_modified(session, model_name, record_id, vals):
#     if session.context.get('connector_no_export'):
#         return
#     if session.env[model_name].browse(record_id).no_stock_sync:
#         return
#     inventory_fields = list(set(vals).intersection(INVENTORY_FIELDS))
#     if inventory_fields:
#         export_product_inventory.delay(session, model_name,
#                                        record_id, fields=inventory_fields,
#                                        priority=20)
#
#
# @job(default_channel='root.carepoint')
# @related_action(action=unwrap_binding)
# def export_product_inventory(session, model_name, record_id, fields=None):
#     """ Export the inventory configuration and quantity of a product. """
#     product = session.env[model_name].browse(record_id)
#     backend_id = product.backend_id.id
#     env = get_environment(session, model_name, backend_id)
#     inventory_exporter = env.get_connector_unit(MedicamentInventoryExporter)
#     return inventory_exporter.run(record_id, fields)
