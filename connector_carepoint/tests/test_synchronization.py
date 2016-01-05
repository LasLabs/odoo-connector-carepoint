# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Dave Lasley <dave@laslabs.com>
#    Copyright: 2015 LasLabs, Inc [https://laslabs.com]
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

from openerp.addons.connector.exception import InvalidDataError
from openerp.addons.carepoint.unit.import_synchronizer import (
    import_batch,
    import_record)
from .common import (mock_api,
                     mock_urlopen_image,
                     SetUpCarepointBase,
                     SetUpCarepointSynchronized,
                     )
from .data_base import carepoint_base_responses


class TestBaseCarepoint(SetUpCarepointBase):

    def test_import_backend(self):
        """ Synchronize initial metadata """
        with mock_api(carepoint_base_responses):
            import_batch(self.session, 'carepoint.store', self.backend_id)

        store_model = self.env['carepoint.store']
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
