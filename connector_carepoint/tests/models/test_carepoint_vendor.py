# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import carepoint_vendor

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class CarepointVendorTestBase(SetUpCarepointBase):

    def setUp(self):
        super(CarepointVendorTestBase, self).setUp()
        self.model = 'carepoint.carepoint.vendor'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'COMPANY': ' Test Vendor ',
            'STATE': 'nv',
            'ID': 123,
        }


class TestCarepointVendorImportMapper(CarepointVendorTestBase):

    def setUp(self):
        super(TestCarepointVendorImportMapper, self).setUp()
        self.Unit = carepoint_vendor.CarepointVendorImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_customer(self):
        """ It should return proper vals """
        res = self.unit.customer(self.record)
        self.assertDictEqual({'customer': False}, res)

    def test_supplier(self):
        """ It should return proper vals """
        res = self.unit.supplier(self.record)
        self.assertDictEqual({'supplier': True}, res)

    def test_is_company(self):
        """ It should return proper vals """
        res = self.unit.is_company(self.record)
        self.assertDictEqual({'is_company': True}, res)

    def test_state_id_search(self):
        """ It should search for NDC """
        with mock.patch.object(self.unit.session, 'env') as env:
            self.unit.state_id(self.record)
            env[''].search.assert_called_once_with(
                [('code', '=', self.record['STATE'].upper())],
                limit=1,
            )

    def test_state_id_return(self):
        """ It should search for NDC """
        with mock.patch.object(self.unit.session, 'env') as env:
            expect = mock.MagicMock()
            env[''].search.return_value = [expect]
            res = self.unit.state_id(self.record)
            self.assertDictEqual(
                {'state_id': expect.id,
                 'country_id': expect.country_id.id},
                res,
            )

    def test_carepoint_id(self):
        """ It should return proper vals """
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual({'carepoint_id': self.record['ID']}, res)

    def test_odoo_id_search(self):
        """ It should search for NDC """
        with mock.patch.object(self.unit.session, 'env') as env:
            self.unit.odoo_id(self.record)
            env[''].search.assert_called_once_with(
                [('name', 'ilike', self.record['COMPANY'].strip())],
                limit=1,
            )

    def test_odoo_id_return(self):
        """ It should search for NDC """
        with mock.patch.object(self.unit.session, 'env') as env:
            expect = [mock.MagicMock()]
            env[''].search.return_value = expect
            res = self.unit.odoo_id(self.record)
            self.assertDictEqual(
                {'odoo_id': expect[0].id},
                res,
            )


class TestCarepointVendorExportMapper(CarepointVendorTestBase):

    def setUp(self):
        super(TestCarepointVendorExportMapper, self).setUp()
        self.Unit = carepoint_vendor.CarepointVendorExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()

    def state(self):
        """ It should return correct vals """
        res = self.unit.state(self.record)
        self.assertDictEqual({'STATE': self.record.state_id.code}, res)
