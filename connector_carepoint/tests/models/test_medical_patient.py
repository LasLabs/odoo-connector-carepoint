# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import medical_patient

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class MedicalPatientTestBase(SetUpCarepointBase):

    def setUp(self):
        super(MedicalPatientTestBase, self).setUp()
        self.model = 'carepoint.medical.patient'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'no_safety_caps_yn': True,
            'pat_id': 1,
            'gender_cd': 'M',
            'birth_date': '2016-09-10',
            'fname': 'FirstName',
            'lname': 'LastName',
        }


class TestMedicalPatientImportMapper(MedicalPatientTestBase):

    def setUp(self):
        super(TestMedicalPatientImportMapper, self).setUp()
        self.Unit = medical_patient.MedicalPatientImportMapper
        self.unit = self.Unit(self.mock_env)

    def _create_patient(self):
        return self.env['medical.patient'].create({
            'name': '%s %s' % (self.record['fname'],
                               self.record['lname']),
            'dob': self.record['birth_date'],
        })

    def test_safety_caps_yn(self):
        """ It should return proper dict vals """
        self.assertDictEqual(
            {'safety_caps_yn': False},
            self.unit.safety_cap_yn(self.record),
        )

    def test_gender_exist(self):
        """ It should return lowercase gender code """
        self.assertDictEqual(
            {'gender': self.record['gender_cd'].lower()},
            self.unit.gender(self.record)
        )

    def test_gender_none(self):
        """ It should return None when no gender """
        self.record['gender_cd'] = False
        self.assertDictEqual(
            {'gender': None},
            self.unit.gender(self.record)
        )

    def test_carepoint_id(self):
        """ It should return lowercase gender code """
        self.assertDictEqual(
            {'carepoint_id': self.record['pat_id']},
            self.unit.carepoint_id(self.record)
        )

    def test_odoo_id(self):
        """ It should return odoo_id of patient with same name """
        expect = self._create_patient()
        res = self.unit.odoo_id(self.record)
        expect = {'odoo_id': expect.id}
        self.assertDictEqual(expect, res)


class TestMedicalPatientImporter(MedicalPatientTestBase):

    def setUp(self):
        super(TestMedicalPatientImporter, self).setUp()
        self.Unit = medical_patient.MedicalPatientImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_after_import_get_unit(self):
        """ It should get unit for address importer """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for'):
            self.unit._after_import(expect)
            self.unit.unit_for.assert_called_once_with(
                medical_patient.CarepointAddressPatientUnit,
                model='carepoint.carepoint.address.patient',
            )

    def test_after_import_get_unit(self):
        """ It should get unit for address importer """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for'):
            self.unit._after_import(expect)
            self.unit.unit_for()._import_addresses.assert_called_once_with(
                self.unit.carepoint_id,
                expect,
            )


class TestMedicalPatientExportMapper(MedicalPatientTestBase):

    def setUp(self):
        super(TestMedicalPatientExportMapper, self).setUp()
        self.Unit = medical_patient.MedicalPatientExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()

    def test_gender_cd(self):
        """ It should return proper export vals dict """
        self.assertDictEqual(
            {'gender_cd': self.record.gender.upper()},
            self.unit.gender_cd(self.record),
        )

    def test_static_defaults(self):
        """ It should return a dict of default values """
        self.assertIsInstance(
            self.unit.static_defaults(self.record),
            dict,
        )

    def test_no_safety_caps_yn(self):
        """ It should return negated safety_caps """
        self.assertFalse(
            self.unit.no_safety_caps_yn(self.record)[
                'no_safety_caps_yn'
            ],
        )
