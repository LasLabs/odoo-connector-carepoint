# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import phone

from ...unit.backend_adapter import CarepointCRUDAdapter

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class CarepointPhoneTestBase(SetUpCarepointBase):

    def setUp(self):
        super(CarepointPhoneTestBase, self).setUp()
        self.model = 'carepoint.carepoint.phone'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.state = self.env.ref('base.state_us_23')
        self.record = {
            'area_code': ' 702 ',
            'phone_no': ' 1234567 ',
            'extension': ' 99 ',
            'phone_id': 123,
        }


class TestCarepointPhoneImportMapper(CarepointPhoneTestBase):

    def setUp(self):
        super(TestCarepointPhoneImportMapper, self).setUp()
        self.Unit = phone.CarepointPhoneImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_phone_all(self):
        """ It should combine all parts of a phone number when existing """
        res = self.unit.phone(self.record)['phone']
        self.assertEqual(
            '+1 (702) 123-4567 x99',
            res,
        )

    def test_phone_no_ext(self):
        """ It should properly handle blank/no ext """
        self.record['extension'] = '    '
        res = self.unit.phone(self.record)['phone']
        self.assertEqual(
            '+1 (702) 123-4567',
            res,
        )

    def test_phone_no_area(self):
        """ It should append default area code of 000 when non-exist """
        self.record['area_code'] = '   '
        res = self.unit.phone(self.record)['phone']
        self.assertEqual(
            '+1 (000) 123-4567 x99',
            res,
        )

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {'carepoint_id': self.record['phone_id']}
        self.assertDictEqual(expect, res)


class TestCarepointPhoneUnit(CarepointPhoneTestBase):

    def setUp(self):
        super(TestCarepointPhoneUnit, self).setUp()
        self.Unit = phone.CarepointPhoneUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_by_filter_unit(self):
        """ It should get units for adapter and importer """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = [None, EndTestException]
            with self.assertRaises(EndTestException):
                self.unit._import_by_filter()
            mk.assert_has_calls([
                mock.call(CarepointCRUDAdapter),
                mock.call(phone.CarepointPhoneImporter),
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


class TestCarepointPhoneExportMapper(CarepointPhoneTestBase):

    def setUp(self):
        super(TestCarepointPhoneExportMapper, self).setUp()
        self.Unit = phone.CarepointPhoneExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()

    def test_phone_id(self):
        """ It should return proper vals dict """
        res = self.unit.phone_id(self.record)
        self.assertDictEqual(
            {'phone_id': self.record.carepoint_id},
            res,
        )
