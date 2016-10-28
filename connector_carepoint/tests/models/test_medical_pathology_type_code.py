# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.connector_carepoint.models import (
    medical_pathology_code_type,
)

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class MedicalPathologyCodeTypeTestBase(SetUpCarepointBase):

    def setUp(self):
        super(MedicalPathologyCodeTypeTestBase, self).setUp()
        self.model = 'carepoint.medical.pathology.code.type'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'icd_cd_type': ' ICD Type Code ',
            'icd_cd_type_desc': ' ICD Type Desc ',
        }


class TestMedicalPathologyCodeTypeImportMapper(
    MedicalPathologyCodeTypeTestBase
):

    def setUp(self):
        super(TestMedicalPathologyCodeTypeImportMapper, self).setUp()
        self.Unit = \
            medical_pathology_code_type.MedicalPathologyCodeTypeImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_odoo_id(self):
        """ It should return odoo_id of pharmacies with same name """
        model = self.env['medical.pathology.code.type']
        expect = model.create({
            'name': self.record['icd_cd_type_desc'].strip(),
        })
        res = self.unit.odoo_id(self.record)
        expect = {'odoo_id': expect.id}
        self.assertDictEqual(expect, res)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {
            'carepoint_id': self.record['icd_cd_type'],
        }
        self.assertDictEqual(expect, res)
