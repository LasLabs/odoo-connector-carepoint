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

import mock

import openerp
import openerp.tests.common as common
from openerp.addons.connector.queue.job import (Job,
                                                OpenERPJobStorage,
                                                )
from openerp.addons.connector.session import ConnectorSession
from .common import mock_api
from .data_base import carepoint_base_responses
from ..unit.import_synchronizer import import_batch, import_record
from ..unit.export_synchronizer import export_record


class TestRelatedActionStorage(common.TransactionCase):
    """ Test related actions on stored jobs """

    def setUp(self):
        super(TestRelatedActionStorage, self).setUp()
        backend_model = self.env['carepoint.backend']
        self.session = ConnectorSession(self.env.cr, self.env.uid,
                                        context=self.env.context)
        warehouse = self.env.ref('stock.warehouse0')
        self.backend = backend_model.create({
            'name': 'Test Carepoint',
            'version': '2.99',
            'server': '127.0.0.1',
            'username': 'laslabs',
            'warehouse_id': warehouse.id,
            'password': '42',
            'sale_prefix': 'CPTST',
        })
        # import the base informations
        with mock_api(carepoint_base_responses):
            import_batch(self.session, 'carepoint.res.company', self.backend.id)
        self.CarepointProduct = self.env['carepoint.product.product']
        self.QueueJob = self.env['queue.job']

    def test_unwrap_binding(self):
        """ Open a related action opening an unwrapped binding """
        product = self.env.ref('product.product_product_7')
        carepoint_product = self.CarepointProduct.create(
            {'openerp_id': product.id,
             'backend_id': self.backend.id})
        stored = self._create_job(export_record, 'carepoint.product.product',
                                  carepoint_product.id)
        expected = {
            'name': mock.ANY,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': product.id,
            'res_model': 'product.product',
        }
        self.assertEquals(stored.open_related_action(), expected)

    def _create_job(self, func, *args):
        job = Job(func=func, args=args)
        storage = OpenERPJobStorage(self.session)
        storage.store(job)
        stored = self.QueueJob.search([('uuid', '=', job.uuid)])
        self.assertEqual(len(stored), 1)
        return stored

    def test_link(self):
        """ Open a related action opening an url on Carepoint """
        self.backend.write({'admin_location': 'http://www.example.com/admin'})
        stored = self._create_job(import_record, 'carepoint.product.product',
                                  self.backend.id, 123456)
        url = 'http://www.example.com/admin/catalog_product/edit/id/123456'
        expected = {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url,
        }
        self.assertEquals(stored.open_related_action(), expected)

    def test_link_no_location(self):
        """ Related action opening an url, admin location is not configured """
        self.backend.write({'admin_location': False})
        self.backend.refresh()
        stored = self._create_job(import_record, 'carepoint.product.product',
                                  self.backend.id, 123456)
        with self.assertRaises(openerp.exceptions.Warning):
            stored.open_related_action()
