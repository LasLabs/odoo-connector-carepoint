# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import address

from ...unit.backend_adapter import CarepointCRUDAdapter

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class CarepointAddressTestBase(SetUpCarepointBase):

    def setUp(self):
        super(CarepointAddressTestBase, self).setUp()
        self.model = 'carepoint.carepoint.address'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.state = self.env.ref('base.state_us_23')
        self.record = {
            'zip': ' 89074 ',
            'zip_plus4': ' 3254 ',
            'state_cd': ' %s ' % self.state.code,
            'addr_id': 123,
        }


class TestCarepointAddressImportMapper(CarepointAddressTestBase):

    def setUp(self):
        super(TestCarepointAddressImportMapper, self).setUp()
        self.Unit = address.CarepointAddressImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_zip(self):
        """ It should return zip code if no plus 4 """
        expect = self.record['zip'].strip()
        self.record['zip_plus4'] = ""
        res = self.unit.zip(self.record)
        self.assertDictEqual({'zip': expect}, res)

    def test_zip_plus(self):
        """ It should join plus4 to zip code if exists """
        expect = '%s-%s' % (self.record['zip'].strip(),
                            self.record['zip_plus4'].strip())
        res = self.unit.zip(self.record)
        self.assertDictEqual({'zip': expect}, res)

    def test_state_id(self):
        """ It should return proper state and country """
        expect = {
            'state_id': self.state.id,
            'country_id': self.state.country_id.id,
        }
        res = self.unit.state_id(self.record)
        self.assertDictEqual(expect, res)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {'carepoint_id': self.record['addr_id']}
        self.assertDictEqual(expect, res)


class TestCarepointAddressUnit(CarepointAddressTestBase):

    def setUp(self):
        super(TestCarepointAddressUnit, self).setUp()
        self.Unit = address.CarepointAddressUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_by_filter_unit(self):
        """ It should get units for adapter and importer """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = [None, EndTestException]
            with self.assertRaises(EndTestException):
                self.unit._import_by_filter()
            mk.assert_has_calls([
                mock.call(CarepointCRUDAdapter),
                mock.call(address.CarepointAddressImporter),
            ])

    def test_import_by_filter_search(self):
        """ It should search adapter for filters """
        expect = {'filter': 'Filter'}
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._import_by_filter(**expect)
            mk().search.assert_called_once_with(
                **expect
            )

    def test_import_by_filter_import(self):
        """ It should run importer on search results """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.return_value = [expect]
            self.unit._import_by_filter()
            mk().run.assert_called_once_with(expect)


class TestCarepointAddressExportMapper(CarepointAddressTestBase):

    def setUp(self):
        super(TestCarepointAddressExportMapper, self).setUp()
        self.Unit = address.CarepointAddressExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()

    def test_addr_id(self):
        """ It should return proper vals dict """
        res = self.unit.addr_id(self.record)
        self.assertDictEqual(
            {'addr_id': self.record.carepoint_id},
            res,
        )
