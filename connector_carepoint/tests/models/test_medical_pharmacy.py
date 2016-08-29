# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import medical_pharmacy

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class MedicalPharmacyTestBase(SetUpCarepointBase):

    def setUp(self):
        super(MedicalPharmacyTestBase, self).setUp()
        self.model = 'carepoint.medical.pharmacy'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'name': 'Test Pharmacy',
            'store_id': 123,
        }


class TestMedicalPharmacyImportMapper(MedicalPharmacyTestBase):

    def setUp(self):
        super(TestMedicalPharmacyImportMapper, self).setUp()
        self.Unit = medical_pharmacy.MedicalPharmacyImportMapper
        self.unit = self.Unit(self.mock_env)

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

    def test_warehouse_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.warehouse_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.stock.warehouse'
            )

    def test_warehouse_id_to_odoo(self):
        """ It should get Odoo record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.warehouse_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['store_id'],
            )

    def test_warehouse_id_return(self):
        """ It should return formatted warehouse_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.warehouse_id(self.record)
            expect = self.unit.binder_for().to_odoo()
            self.assertDictEqual({'warehouse_id': expect}, res)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = 6789
        self.record['store_id'] = expect
        res = self.unit.carepoint_id(self.record)
        expect = {'carepoint_id': expect}
        self.assertDictEqual(expect, res)


class TestMedicalPharmacyImporter(MedicalPharmacyTestBase):

    def setUp(self):
        super(TestMedicalPharmacyImporter, self).setUp()
        self.Unit = medical_pharmacy.MedicalPharmacyImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['store_id'],
                    'carepoint.stock.warehouse',
                ),
            ])
