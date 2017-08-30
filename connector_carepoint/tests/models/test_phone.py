# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import phone

from ...unit.backend_adapter import CarepointAdapter

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


class TestCarepointPhone(CarepointPhoneTestBase):

    def setUp(self):
        super(TestCarepointPhone, self).setUp()
        self.model = self.env['carepoint.phone']
        self.phone_field = 'mobile'

    def new_partner(self):
        return self.env['res.partner'].create({
            'name': 'Test Partner',
            'phone': 'phone',
            'fax': 'fax',
            'mobile': 'mobile',
        })

    def new_phone(self, partner=None, phone_field='mobile'):
        if partner is None:
            partner = self.new_partner()
        return self.model.create({
            'phone': partner[phone_field],
            'partner_field_name': phone_field,
            'partner_id': partner.id,
        })

    def test_sync_partner(self):
        """ It should set proper attributes on partner when updated """
        partner = self.new_partner()
        fields = 'phone', 'mobile', 'fax'
        phones = []
        for field in fields:
            expect = 'new %s' % field
            phones.append(self.new_phone(partner, field))
            phones[-1].write({'phone': expect})
        for field in fields:
            self.assertEqual('new %s' % field, partner[field])


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
                mock.call(CarepointAdapter),
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
        self.phone = {
            'code': '1',
            'area': '888',
            'phone': '1234567',
            'ext': '123',
        }
        self.record.phone = '%(area)s%(phone)s x%(ext)s' % self.phone
        self.record.partner_id.country_id.code = False

    def test_phone_none(self):
        """ It should not try to parse a blank number """
        self.record.phone = False
        res = self.unit.phone(self.record)
        self.assertFalse(res)

    def test_phone_area_code(self):
        """ It should return proper area code """
        res = self.unit.phone(self.record)
        self.assertEqual(self.phone['area'], res['area_code'])

    def test_phone_national(self):
        """ It should return proper national number """
        res = self.unit.phone(self.record)
        self.assertEqual(self.phone['phone'], res['phone_no'])

    def test_phone_extension(self):
        """ It should return proper extension """
        res = self.unit.phone(self.record)
        self.assertEqual(self.phone['ext'], res['extension'])

    def test_phone_extension_none(self):
        """ It should handle blank extensions """
        self.record.phone = '%(area)s%(phone)s' % self.phone
        res = self.unit.phone(self.record)
        self.assertEqual('', res['extension'])

    def test_phone_id(self):
        """ It should return proper vals dict """
        res = self.unit.phone_id(self.record)
        self.assertDictEqual(
            {'phone_id': self.record.carepoint_id},
            res,
        )
