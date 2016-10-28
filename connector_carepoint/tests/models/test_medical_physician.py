# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import medical_physician

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class MedicalPhysicianTestBase(SetUpCarepointBase):

    def setUp(self):
        super(MedicalPhysicianTestBase, self).setUp()
        self.model = 'carepoint.medical.physician'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'no_safety_caps_yn': True,
            'md_id': 1,
            'gender_cd': 'M',
            'birth_date': '2016-09-10',
            'fname': 'FirstName',
            'lname': 'LastName',
            'email': 'email@test.com',
        }


class TestMedicalPhysicianImportMapper(MedicalPhysicianTestBase):

    def setUp(self):
        super(TestMedicalPhysicianImportMapper, self).setUp()
        self.Unit = medical_physician.MedicalPhysicianImportMapper
        self.unit = self.Unit(self.mock_env)

    def _create_physician(self):
        return self.env['medical.physician'].create({
            'name': '%s %s' % (self.record['fname'],
                               self.record['lname']),
            'email': self.record['email'],
        })

    def test_carepoint_id(self):
        """ It should return lowercase gender code """
        self.assertDictEqual(
            {'carepoint_id': self.record['md_id']},
            self.unit.carepoint_id(self.record)
        )

    def test_odoo_id(self):
        """ It should return odoo_id of physician with same name """
        expect = self._create_physician()
        res = self.unit.odoo_id(self.record)
        expect = {'odoo_id': expect.id}
        self.assertDictEqual(expect, res)


class TestMedicalPhysicianImporter(MedicalPhysicianTestBase):

    def setUp(self):
        super(TestMedicalPhysicianImporter, self).setUp()
        self.Unit = medical_physician.MedicalPhysicianImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_after_import_get_unit(self):
        """ It should get unit for importers """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for'):
            self.unit._after_import(expect)
            self.unit.unit_for.assert_has_calls([
                mock.call(
                    medical_physician.CarepointAddressPhysicianUnit,
                    model='carepoint.carepoint.address.physician',
                ),
                mock.call()._import_addresses(
                    self.unit.carepoint_id,
                    expect,
                ),
                mock.call(
                    medical_physician.CarepointPhonePhysicianUnit,
                    model='carepoint.carepoint.phone.physician',
                ),
                mock.call()._import_phones(
                    self.unit.carepoint_id,
                    expect,
                ),
            ])


class TestMedicalPhysicianExportMapper(MedicalPhysicianTestBase):

    def setUp(self):
        super(TestMedicalPhysicianExportMapper, self).setUp()
        self.Unit = medical_physician.MedicalPhysicianExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()


class TestMedicalPhysicianExporter(MedicalPhysicianTestBase):

    def setUp(self):
        super(TestMedicalPhysicianExporter, self).setUp()
        self.Unit = medical_physician.MedicalPhysicianExporter
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()
        self.unit.binding_record = self.record

    def test_after_export_address_get_by_partner(self):
        """ It should get addresses by partner """
        with mock.patch.object(self.unit.session, 'env') as env:
            self.unit._after_export()
            get = env['']._get_by_partner
            call = mock.call(
                self.record.commercial_partner_id,
                edit=True,
                recurse=True,
            )
            get.assert_has_calls([call, call])
