# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import stock_warehouse

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class StockWarehouseTestBase(SetUpCarepointBase):

    def setUp(self):
        super(StockWarehouseTestBase, self).setUp()
        self.model = 'carepoint.stock.warehouse'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'store_id': 123,
            'name': ' warehouse ',
        }


class TestStockWarehouseImportMapper(StockWarehouseTestBase):

    def setUp(self):
        super(TestStockWarehouseImportMapper, self).setUp()
        self.Unit = stock_warehouse.StockWarehouseImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_code(self):
        expect = {'code': self.record['name'].strip()}
        res = self.unit.code(self.record)
        self.assertDictEqual(expect, res)

    def test_is_pharmacy(self):
        expect = {'is_pharmacy': True}
        res = self.unit.is_pharmacy(self.record)
        self.assertDictEqual(expect, res)

    def test_carepoint_id(self):
        expect = {'carepoint_id': self.record['store_id']}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_partner_id_company_id_get_binder(self):
        """ It should get binder for pharmacy """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id_company_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.pharmacy'
            )

    def test_partner_id_company_id_to_odoo(self):
        """ It should get Odoo record for pharmacy """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id_company_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['store_id'], browse=True,
            )

    def test_partner_id_company_id_return(self):
        """ It should return formatted partner_id_company_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.partner_id_company_id(self.record)
            expect = self.unit.binder_for().to_odoo()
            expect = {
                'company_id': expect.company_id.id,
                'partner_id': expect.partner_id.id,
            }
            self.assertDictEqual(expect, res)

    def test_route_ids(self):
        expect = ['route_ids', 'prescription_route_id', 'otc_route_id']
        res = self.unit.route_ids(self.record)
        for key in res.keys():
            self.assertIn(key, expect)
