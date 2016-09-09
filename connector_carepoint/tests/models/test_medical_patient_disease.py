# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import medical_patient_disease

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class MedicalPatientDiseaseTestBase(SetUpCarepointBase):

    def setUp(self):
        super(MedicalPatientDiseaseTestBase, self).setUp()
        self.model = 'carepoint.medical.patient.disease'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'pat_id': 1,
            'caring_md_id': 2,
            'ptdx_id': 3,
            'icd9': ' 520.0 ',
        }


class TestMedicalPatientDiseaseImportMapper(MedicalPatientDiseaseTestBase):

    def setUp(self):
        super(TestMedicalPatientDiseaseImportMapper, self).setUp()
        self.Unit = medical_patient_disease.MedicalPatientDiseaseImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_pathology_id(self):
        """ It should get ICD9 pathology of right code """
        code_type_id = self.env.ref('medical_pathology.pathology_code_01')
        expect = self.env['medical.pathology'].create({
            'name': 'Pathology',
            'code_type_id': code_type_id.id,
            'code': self.record['icd9'].strip(),
        })
        res = self.unit.pathology_id(self.record)
        self.assertDictEqual(
            {'pathology_id': expect.id},
            res,
        )

    def test_patient_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.patient_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.patient'
            )

    def test_patient_id_to_odoo(self):
        """ It should get Odoo record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.patient_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['pat_id'],
            )

    def test_patient_id_return(self):
        """ It should return formatted patient_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.patient_id(self.record)
            expect = self.unit.binder_for().to_odoo()
            self.assertDictEqual({'patient_id': expect}, res)

    def test_physician_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.physician_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.physician'
            )

    def test_physician_id_to_odoo(self):
        """ It should get Odoo record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.physician_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['caring_md_id'],
            )

    def test_physician_id_return(self):
        """ It should return formatted physician_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.physician_id(self.record)
            expect = self.unit.binder_for().to_odoo()
            self.assertDictEqual({'physician_id': expect}, res)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {
            'carepoint_id': self.record['ptdx_id'],
        }
        self.assertDictEqual(expect, res)


class TestMedicalPatientDiseaseUnit(MedicalPatientDiseaseTestBase):

    def setUp(self):
        super(TestMedicalPatientDiseaseUnit, self).setUp()
        self.Unit = medical_patient_disease.MedicalPatientDiseaseUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_by_patient_unit_for_adapter(self):
        """ It should get unit for adapter """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._import_by_patient(True)
            mk.assert_has_calls([
                mock.call(
                    medical_patient_disease.MedicalPatientDiseaseAdapter,
                ),
                mock.call(
                    medical_patient_disease.MedicalPatientDiseaseImporter,
                ),
            ])

    def test_import_by_patient_search(self):
        """ It should search adapter for unit """
        expect = 'expect'
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_by_patient(expect)
            mk().search.assert_called_once_with(
                pat_id=expect,
            )

    def test_import_by_patient_imports(self):
        """ It should run importer on records """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            expect = mock.MagicMock()
            adapter = mock.MagicMock()
            adapter.search.return_value = [True]
            mk.side_effect = [adapter, expect]
            self.unit._import_by_patient(True)
            expect.run.assert_called_once_with(
                adapter.search()[0]
            )


class TestMedicalPatientDiseaseImporter(MedicalPatientDiseaseTestBase):

    def setUp(self):
        super(TestMedicalPatientDiseaseImporter, self).setUp()
        self.Unit = medical_patient_disease.MedicalPatientDiseaseImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_after_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            with mock.patch.object(self.unit, 'unit_for'):
                self.unit._import_dependencies()
                mk.assert_has_calls([
                    mock.call(
                        self.record['pat_id'],
                        'carepoint.medical.patient',
                    ),
                    mock.call(
                        self.record['caring_md_id'],
                        'carepoint.medical.physician',
                    ),
                ])

    def test_after_import_dependencies_pathology_unit(self):
        """ It should get unit for pathology """
        with mock.patch.object(self.unit, '_import_dependency'):
            with mock.patch.object(self.unit, 'unit_for'):
                self.unit._import_dependencies()
                self.unit.unit_for.assert_has_calls([
                    mock.call(
                        medical_patient_disease.MedicalPathologyUnit,
                        'carepoint.medical.pathology',
                    ),
                    mock.call()._import_by_code(
                        self.record['icd9'].strip(),
                    )
                ])
