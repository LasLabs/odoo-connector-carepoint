# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import phone_physician

from ...unit.backend_adapter import CarepointAdapter

from ..common import SetUpCarepointBase


_file = 'odoo.addons.connector_carepoint.models.phone_physician'


class EndTestException(Exception):
    pass


class PhonePhysicianTestBase(SetUpCarepointBase):

    def setUp(self):
        super(PhonePhysicianTestBase, self).setUp()
        self.model = 'carepoint.phone.physician'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'md_id': 1,
            'phone_id': 2,
        }


class TestPhonePhysicianImportMapper(PhonePhysicianTestBase):

    def setUp(self):
        super(TestPhonePhysicianImportMapper, self).setUp()
        self.Unit = phone_physician.CarepointPhonePhysicianImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_partner_id_get_binder(self):
        """ It should get binder for physician """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.physician'
            )

    def test_partner_id_to_odoo(self):
        """ It should get Odoo record for physician """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['md_id'], browse=True,
            )

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {
            'carepoint_id': '%d,%d' % (
                self.record['md_id'],
                self.record['phone_id'],
            ),
        }
        self.assertDictEqual(expect, res)


class TestPhonePhysicianImporter(PhonePhysicianTestBase):

    def setUp(self):
        super(TestPhonePhysicianImporter, self).setUp()
        self.Unit = phone_physician.CarepointPhonePhysicianImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    @mock.patch('%s.CarepointPhoneAbstractImporter' % _file,
                spec=phone_physician.CarepointPhoneAbstractImporter,
                )
    def test_import_dependencies_import(self, _super):
        """ It should import all dependencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['md_id'],
                    'carepoint.medical.physician',
                ),
            ])


class TestCarepointPhonePhysicianUnit(PhonePhysicianTestBase):

    def setUp(self):
        super(TestCarepointPhonePhysicianUnit, self).setUp()
        self.Unit = phone_physician.CarepointPhonePhysicianUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_phones_unit(self):
        """ It should get units for adapter and importer """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = [None, EndTestException]
            with self.assertRaises(EndTestException):
                self.unit._import_phones(None, None)
            mk.assert_has_calls([
                mock.call(CarepointAdapter),
                mock.call(
                    phone_physician.CarepointPhonePhysicianImporter,
                ),
            ])

    def test_import_phones_search(self):
        """ It should search adapter for filters """
        physician = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._import_phones(physician, None)
            mk().search.assert_called_once_with(
                md_id=physician,
            )

    def test_import_phones_import(self):
        """ It should run importer on search results """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.return_value = [expect]
            self.unit._import_phones(1, None)
            mk().run.assert_called_once_with(expect)


class TestCarepointPhonePhysicianExportMapper(
    PhonePhysicianTestBase
):

    def setUp(self):
        super(TestCarepointPhonePhysicianExportMapper, self).setUp()
        self.Unit = \
            phone_physician.CarepointPhonePhysicianExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()

    def test_md_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.md_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.physician'
            )

    def test_md_id_to_backend(self):
        """ It should get backend record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_backend.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.md_id(self.record)
            self.unit.binder_for().to_backend.assert_called_once_with(
                self.record.res_id,
            )

    def test_md_id_return(self):
        """ It should return formatted md_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.md_id(self.record)
            expect = self.unit.binder_for().to_backend()
            self.assertDictEqual({'md_id': expect}, res)
