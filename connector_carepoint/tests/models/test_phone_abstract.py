# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import phone_abstract

from ..common import SetUpCarepointBase

try:
    from carepoint.models.phone_mixin import EnumPhoneType
except ImportError:
    pass


class EndTestException(Exception):
    pass


class PhoneAbstractTestBase(SetUpCarepointBase):

    def setUp(self):
        super(PhoneAbstractTestBase, self).setUp()
        self.model = 'carepoint.phone.abstract'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'phone_id': 123,
            'phone_type_cn': EnumPhoneType.home,
        }

    def new_partner(self):
        return self.env['res.partner'].create({
            'name': 'Partner',
            'phone': 'phone',
            'fax': 'fax',
            'mobile': 'mobile',
        })

    def new_patient(self, partner=None):
        if not partner:
            partner = self.new_partner()
        return self.env['medical.patient'].create({
            'partner_id': partner.id,
        })


class TestCarepointPhoneAbstract(PhoneAbstractTestBase):

    def setUp(self):
        super(TestCarepointPhoneAbstract, self).setUp()
        self.model = self.env['carepoint.phone.patient']

    def new_phone(self, partner=None, field='phone'):
        if partner is None:
            partner = self.new_partner()
        vals = {
            'partner_field_name': field,
            'phone': partner[field],
        }
        if partner:
            vals['partner_id'] = partner.id
        return self.env['carepoint.phone'].create(vals)

    def new_patient_phone(self):
        self.patient = self.new_patient()
        self.phone = self.new_phone(self.patient.partner_id)
        return self.model.create({
            'partner_id': self.patient.partner_id.id,
            'phone_id': self.phone.id,
            'res_model': 'medical.patient',
        })

    def test_compute_partner_id(self):
        """ It should retrieve the partner_id from associated phone """
        phone = self.new_patient_phone()
        self.assertEqual(
            phone.partner_id,
            self.phone.partner_id,
        )

    def test_set_partner_id_blank_phone(self):
        """ It should sync phone values to partner when no phone """
        phone = self.new_patient_phone()
        partner = self.new_partner()
        phone.write({'partner_id': partner.id})
        self.assertEqual(
            phone.phone,
            partner.phone,
        )

    def test_set_partner_id_with_phone(self):
        """ It should set the phone vals from partner """
        phone = self.new_patient_phone()
        partner = self.new_partner()
        expect = '123 Partner St'
        partner.phone = expect
        phone.write({'partner_id': partner.id})
        self.assertEqual(
            expect,
            phone.phone,
        )

    def test_medical_entity_id(self):
        """ It should return patient record """
        phone = self.new_patient_phone()
        self.assertEqual(
            self.patient,
            phone.medical_entity_id,
        )

    def test_compute_res_id(self):
        """ It should compute the Resource ID for record """
        phone = self.new_patient_phone()
        self.assertEqual(
            self.patient.id,
            phone.res_id,
        )

    def test_compute_res_id_empty(self):
        """ It should continue when resource isn't known """
        phone = self.new_patient_phone()
        phone.res_model = False
        self.assertFalse(
            phone.res_id,
        )

    def test_get_by_partner_existing_phone(self):
        """ It should return partner associated with existing phone """
        phone = self.new_patient_phone()
        res = phone._get_by_partner(phone.partner_id, False, False)
        self.assertEqual(phone, res)

    def test_get_by_partner_create(self):
        """ It should create new phones when non-existing """
        patient = self.new_patient()
        res = self.model._get_by_partner(patient.partner_id, True, False)
        for phone in res:
            self.assertEqual(patient.partner_id, phone.partner_id)

    def test_get_by_partner_create_fields(self):
        """ It should create new phones with proper field names """
        patient = self.new_patient()
        res = self.model._get_by_partner(patient.partner_id, True, False)
        found_vals = []
        for phone in res:
            self.assertEqual(
                patient[phone.partner_field_name],
                phone.phone,
            )
            found_vals.append(phone.partner_field_name)
        self.assertEqual(
            3, len(found_vals), 'Did not create proper amount of phones',
        )

    def test_get_by_partner_edit(self):
        """ It should update vals on phone when edit and existing """
        expect = {
            'phone': 'phone1',
            'mobile': 'mobile1',
            'fax': 'fax1',
        }
        partner = self.new_partner()
        partner.write(expect)
        res = self.model._get_by_partner(
            partner, True, False,
        )
        found_vals = []
        for phone in res:
            self.assertEqual(
                partner[phone.partner_field_name],
                phone.phone,
            )
            found_vals.append(phone.partner_field_name)
        self.assertEqual(
            3, len(found_vals), 'Did not create proper amount of phones',
        )

    def test_get_by_partner_recurse(self):
        """ It should recurse into children when edit and recurse """
        parent, child = self.new_patient(), self.new_patient()
        child.parent_id = parent.partner_id.id
        self.model._get_by_partner(parent.partner_id, True, True)
        phone = self.model.search([('partner_id', '=', child.partner_id.id)])
        self.assertTrue(len(phone))

    def test_compute_partner_id(self):
        phone = self.new_patient_phone()
        self.assertEqual(
            self.patient.partner_id.id,
            phone.partner_id.id,
        )


class TestPhoneAbstractImportMapper(PhoneAbstractTestBase):

    def setUp(self):
        super(TestPhoneAbstractImportMapper, self).setUp()
        self.Unit = phone_abstract.CarepointPhoneAbstractImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_partner_id_empty(self):
        """ It should return partner when empty phone """
        patient = self.new_patient()
        res = self.unit.partner_id(
            self.record, patient,
        )
        expect = {'partner_id': patient.commercial_partner_id.id}
        self.assertDictEqual(expect, res)

    def test_phone_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.phone_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.carepoint.phone'
            )

    def test_phone_id_to_odoo(self):
        """ It should get Odoo record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.phone_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['phone_id'],
            )

    def test_phone_id_return(self):
        """ It should return formatted phone_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.phone_id(self.record)
            expect = self.unit.binder_for().to_odoo()
            self.assertDictEqual({'phone_id': expect}, res)

    def test_res_model_and_id(self):
        """ It should return values dict for medical entity """
        entity = mock.MagicMock()
        expect = {
            'res_id': entity.id,
            'res_model': entity._name,
        }
        res = self.unit.res_model_and_id(None, entity)
        self.assertDictEqual(expect, res)

    def test_partner_field_name(self):
        """ It should return field name for phone type"""
        expect = {
            'partner_field_name': self.unit.PHONE_MAP['home'],
        }
        res = self.unit.partner_field_name(self.record)
        self.assertDictEqual(expect, res)


class TestPhoneAbstractImporter(PhoneAbstractTestBase):

    def setUp(self):
        super(TestPhoneAbstractImporter, self).setUp()
        self.Unit = phone_abstract.CarepointPhoneAbstractImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['phone_id'],
                    'carepoint.carepoint.phone',
                ),
            ])


class TestPhoneAbstractExportMapper(PhoneAbstractTestBase):

    def setUp(self):
        super(TestPhoneAbstractExportMapper, self).setUp()
        self.Unit = phone_abstract.CarepointPhoneAbstractExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()

    def test_phone_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.phone_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.carepoint.phone'
            )

    def test_phone_id_to_backend(self):
        """ It should get backend record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_backend.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.phone_id(self.record)
            self.unit.binder_for().to_backend.assert_called_once_with(
                self.record.phone_id.id,
            )

    def test_phone_id_return(self):
        """ It should return formatted phone_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.phone_id(self.record)
            expect = self.unit.binder_for().to_backend()
            self.assertDictEqual({'phone_id': expect}, res)

    def test_phone_type_cn(self):
        """ It should return the proper Enum val """
        self.record.partner_field_name = 'mobile'
        res = self.unit.phone_type_cn(self.record)
        expect = EnumPhoneType['mobile']
        self.assertDictEqual({'phone_type_cn': expect.value}, res)

    def test_static_defaults(self):
        """ It should return a dict of default values """
        self.assertIsInstance(
            self.unit.static_defaults(self.record),
            dict,
        )


class TestPhoneAbstractExporter(PhoneAbstractTestBase):

    def setUp(self):
        super(TestPhoneAbstractExporter, self).setUp()
        self.Unit = phone_abstract.CarepointPhoneAbstractExporter
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()
        self.unit.binding_record = self.record

    def test_export_dependencies(self):
        """ It should export all dependencies """
        with mock.patch.object(self.unit, '_export_dependency') as mk:
            self.unit._export_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record.phone_id,
                    'carepoint.carepoint.phone',
                ),
            ])
