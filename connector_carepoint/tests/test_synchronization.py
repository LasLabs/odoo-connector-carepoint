# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.connector_carepoint.unit.import_synchronizer import (
    import_batch,
)
from .common import (mock_api,
                     SetUpCarepointBase,
                     )
from .data_base import carepoint_base_responses


class TestBaseCarepoint(SetUpCarepointBase):

    def test_import_backend(self):
        """ Synchronize initial metadata """
        with mock_api(carepoint_base_responses):
            import_batch(
                self.session, 'carepoint.medical.pharmacy', self.backend_id
            )

        store_model = self.env['carepoint.medical.pharmacy']
        stores = store_model.search([('backend_id', '=', self.backend_id)])
        self.assertEqual(len(stores), 2)


# class TestImportCarepoint(SetUpCarepointSynchronized):
#     """ Test the imports from a Carepoint Mock. """
#
#     def test_import_product_category(self):
#         """ Import of a product category """
#         backend_id = self.backend_id
#         with mock_api(carepoint_base_responses):
#             import_record(self.session, 'carepoint.product.category',
#                           backend_id, 1)
#
#         category_model = self.env['carepoint.product.category']
#         category = category_model.search([('backend_id', '=', backend_id)])
#         self.assertEqual(len(category), 1)
#
