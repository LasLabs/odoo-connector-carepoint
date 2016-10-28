# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import medical_pathology

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class MedicalPathologyTestBase(SetUpCarepointBase):

    def setUp(self):
        super(MedicalPathologyTestBase, self).setUp()
        self.model = 'carepoint.medical.pathology'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'icd_cd': ' ICD Code ',
            'icd_cd_type': ' ICD Type Code ',
        }


class TestMedicalPathologyImportMapper(MedicalPathologyTestBase):

    def setUp(self):
        super(TestMedicalPathologyImportMapper, self).setUp()
        self.Unit = medical_pathology.MedicalPathologyImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_odoo_id(self):
        """ It should return odoo_id of recs with same code & type """
        with mock.patch.object(self.unit, 'binder_for'):
            model_obj = self.env['carepoint.medical.pathology.code.type']
            code_type_id = model_obj.create({
                'name': self.record['icd_cd_type'].strip(),
            })
            self.unit.binder_for().to_odoo.return_value = code_type_id.id
            expect = self.env['medical.pathology'].create({
                'name': 'Pathology',
                'code_type_id': code_type_id.id,
                'code': self.record['icd_cd'].strip(),
            })
            res = self.unit.odoo_id(self.record)
            expect = {'odoo_id': expect.id}
            self.assertDictEqual(expect, res)

    def test_code_type_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.code_type_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.pathology.code.type'
            )

    def test_code_type_id_to_odoo(self):
        """ It should get Odoo record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.code_type_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['icd_cd_type'].strip(),
            )

    def test_code_type_id_return(self):
        """ It should return formatted code_type_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.code_type_id(self.record)
            expect = self.unit.binder_for().to_odoo()
            self.assertDictEqual({'code_type_id': expect}, res)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {
            'carepoint_id': '%s,%s' % (
                self.record['icd_cd'].strip(),
                self.record['icd_cd_type'].strip(),
            ),
        }
        self.assertDictEqual(expect, res)


class TestMedicalPathologyUnit(MedicalPathologyTestBase):

    def setUp(self):
        super(TestMedicalPathologyUnit, self).setUp()
        self.Unit = medical_pathology.MedicalPathologyUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_by_code_unit_for_adapter(self):
        """ It should get unit for adapter """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._import_by_code(True)
            mk.assert_has_calls([
                mock.call(
                    medical_pathology.MedicalPathologyAdapter,
                ),
                mock.call(
                    medical_pathology.MedicalPathologyImporter,
                ),
            ])

    def test_import_by_code_search(self):
        """ It should search adapter for unit """
        expect = 'expect'
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_by_code(expect)
            mk().search.assert_called_once_with(
                icd_cd=expect,
            )

    def test_import_by_code_imports(self):
        """ It should run importer on records """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            expect = mock.MagicMock()
            adapter = mock.MagicMock()
            adapter.search.return_value = [True]
            mk.side_effect = [adapter, expect]
            self.unit._import_by_code(True)
            expect.run.assert_called_once_with(
                adapter.search()[0]
            )


class TestMedicalPathologyImporter(MedicalPathologyTestBase):

    def setUp(self):
        super(TestMedicalPathologyImporter, self).setUp()
        self.Unit = medical_pathology.MedicalPathologyImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_after_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['icd_cd_type'].strip(),
                    'carepoint.medical.pathology.code.type',
                ),
            ])
