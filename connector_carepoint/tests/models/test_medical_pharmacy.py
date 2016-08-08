# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.connector_carepoint.models import medical_pharmacy

from ..common import SetUpCarepointBase


class TestMedicalPharmacy(SetUpCarepointBase):

    def setUp(self):
        super(TestMedicalPharmacy, self).setUp()
        self.Unit = medical_pharmacy.MedicalPharmacyImportMapper
        self.model = 'carepoint.medical.pharmacy'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.unit = self.Unit(self.mock_env)
        self.record = {
            'name': 'Test Pharmacy',
        }

    def test_odoo_id(self):
        """ It should return odoo_id of pharmacies with same name """
        expect = self.env[self.model.replace('carepoint.', '')].create(
            self.record
        )
        res = self.unit.odoo_id(self.record)
        expect = {'odoo_id': expect.id}
        self.assertDictEqual(expect, res)

    def test_parent_id(self):
        """ It should return id of backend_record companie's partner """
        res = self.unit.parent_id(self.record)
        expect = {
            'parent_id':
                self.unit.backend_record.company_id.partner_id.id,
        }
        self.assertDictEqual(expect, res)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = 6789
        self.record['store_id'] = expect
        res = self.unit.carepoint_id(self.record)
        expect = {'carepoint_id': expect}
        self.assertDictEqual(expect, res)
