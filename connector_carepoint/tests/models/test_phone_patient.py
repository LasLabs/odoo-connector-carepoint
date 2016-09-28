# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import phone_patient

from ...unit.backend_adapter import CarepointCRUDAdapter

from ..common import SetUpCarepointBase


_file = 'openerp.addons.connector_carepoint.models.phone_patient'


class EndTestException(Exception):
    pass


class PhonePatientTestBase(SetUpCarepointBase):

    def setUp(self):
        super(PhonePatientTestBase, self).setUp()
        self.model = 'carepoint.phone.patient'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'pat_id': 1,
            'phone_id': 2,
        }


class TestPhonePatientImportMapper(PhonePatientTestBase):

    def setUp(self):
        super(TestPhonePatientImportMapper, self).setUp()
        self.Unit = phone_patient.CarepointPhonePatientImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_partner_id_get_binder(self):
        """ It should get binder for patient """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.patient'
            )

    def test_partner_id_to_odoo(self):
        """ It should get Odoo record for patient """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['pat_id'], browse=True,
            )

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {
            'carepoint_id': '%d,%d' % (
                self.record['pat_id'],
                self.record['phone_id'],
            ),
        }
        self.assertDictEqual(expect, res)


class TestPhonePatientImporter(PhonePatientTestBase):

    def setUp(self):
        super(TestPhonePatientImporter, self).setUp()
        self.Unit = phone_patient.CarepointPhonePatientImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    @mock.patch('%s.CarepointPhoneAbstractImporter' % _file,
                spec=phone_patient.CarepointPhoneAbstractImporter,
                )
    def test_import_dependencies_import(self, _super):
        """ It should import all dependencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['pat_id'],
                    'carepoint.medical.patient',
                ),
            ])


class TestCarepointPhonePatientUnit(PhonePatientTestBase):

    def setUp(self):
        super(TestCarepointPhonePatientUnit, self).setUp()
        self.Unit = phone_patient.CarepointPhonePatientUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_phones_unit(self):
        """ It should get units for adapter and importer """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = [None, EndTestException]
            with self.assertRaises(EndTestException):
                self.unit._import_phones(None, None)
            mk.assert_has_calls([
                mock.call(CarepointCRUDAdapter),
                mock.call(
                    phone_patient.CarepointPhonePatientImporter,
                ),
            ])

    def test_import_phones_search(self):
        """ It should search adapter for filters """
        patient = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._import_phones(patient, None)
            mk().search.assert_called_once_with(
                pat_id=patient,
            )

    def test_import_phones_import(self):
        """ It should run importer on search results """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.return_value = [expect]
            self.unit._import_phones(1, None)
            mk().run.assert_called_once_with(expect)


class TestPhonePatientExportMapper(PhonePatientTestBase):

    def setUp(self):
        super(TestPhonePatientExportMapper, self).setUp()
        self.Unit = phone_patient.CarepointPhonePatientExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()

    def test_pat_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.pat_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.patient'
            )

    def test_pat_id_to_backend(self):
        """ It should get backend record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_backend.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.pat_id(self.record)
            self.unit.binder_for().to_backend.assert_called_once_with(
                self.record.res_id,
            )

    def test_pat_id_return(self):
        """ It should return formatted pat_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.pat_id(self.record)
            expect = self.unit.binder_for().to_backend()
            self.assertDictEqual({'pat_id': expect}, res)
