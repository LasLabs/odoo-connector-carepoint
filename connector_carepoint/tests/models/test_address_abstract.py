# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import address_abstract

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class AddressAbstractTestBase(SetUpCarepointBase):

    def setUp(self):
        super(AddressAbstractTestBase, self).setUp()
        self.model = 'carepoint.address.abstract'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'addr_id': 123,
        }

    def new_partner(self):
        return self.env['res.partner'].create({'name': 'Partner'})

    def new_patient(self, partner=None):
        if not partner:
            partner = self.new_partner()
        return self.env['medical.patient'].create({
            'partner_id': partner.id,
        })


class TestCarepointAddressAbstract(AddressAbstractTestBase):

    def setUp(self):
        super(TestCarepointAddressAbstract, self).setUp()
        self.model = self.env['carepoint.address.patient']

    def new_address(self, partner=None):
        if partner is None:
            partner = self.new_partner()
        vals = {
            'street': 'Street',
            'street2': 'Street 2',
            'zip': 89074,
            'state_id': self.env.ref('base.state_us_23').id,
            'country_id': self.env.ref('base.us').id,
        }
        if partner:
            vals['partner_id'] = partner.id
        return self.env['carepoint.address'].create(vals)

    def new_patient_address(self):
        self.patient = self.new_patient()
        self.address = self.new_address(self.patient.partner_id)
        return self.model.create({
            'partner_id': self.patient.partner_id.id,
            'address_id': self.address.id,
            'res_model': 'medical.patient',
        })

    def test_compute_partner_id(self):
        """ It should retrieve the partner_id from associated address """
        address = self.new_patient_address()
        self.assertEqual(
            address.partner_id,
            self.address.partner_id,
        )

    def test_set_partner_id_blank_address(self):
        """ It should sync address values to partner when no address """
        address = self.new_patient_address()
        partner = self.new_partner()
        address.write({'partner_id': partner.id})
        self.assertEqual(
            address.street,
            partner.street,
        )

    def test_set_partner_id_with_address(self):
        """ It should set the address vals from partner """
        address = self.new_patient_address()
        partner = self.new_partner()
        expect = '123 Partner St'
        partner.street = expect
        address.write({'partner_id': partner.id})
        self.assertEqual(
            expect,
            address.street,
        )

    def test_medical_entity_id(self):
        """ It should return patient record """
        address = self.new_patient_address()
        self.assertEqual(
            self.patient,
            address.medical_entity_id,
        )

    def test_compute_res_id(self):
        """ It should compute the Resource ID for record """
        address = self.new_patient_address()
        self.assertEqual(
            self.patient.id,
            address.res_id,
        )

    def test_compute_res_id_empty(self):
        """ It should continue when resource isn't known """
        address = self.new_patient_address()
        address.res_model = False
        self.assertFalse(
            address.res_id,
        )

    def test_get_by_partner_existing_address(self):
        """ It should return partner associated with existing address """
        address = self.new_patient_address()
        res = address._get_by_partner(address.partner_id, False, False)
        self.assertEqual(address, res)

    def test_get_by_partner_create(self):
        """ It should create new address when non-exist and edit """
        patient = self.new_patient()
        res = self.model._get_by_partner(patient.partner_id, True, False)
        self.assertEqual(patient.partner_id, res.partner_id)

    def test_get_by_partner_edit(self):
        """ It should update vals on address when edit and existing """
        expect = 'expect'
        address = self.new_patient_address()
        address.partner_id.street = expect
        res = address._get_by_partner(address.partner_id, True, False)
        self.assertEqual(expect, res.street)

    def test_get_by_partner_recurse(self):
        """ It should recurse into children when edit and recurse """
        parent, child = self.new_patient(), self.new_patient()
        child.parent_id = parent.partner_id.id
        self.model._get_by_partner(parent.partner_id, True, True)
        address = self.model.search([('partner_id', '=', child.partner_id.id)])
        self.assertTrue(len(address))

    def test_compute_partner_id(self):
        address = self.new_patient_address()
        self.assertEqual(
            self.patient.partner_id.id,
            address.partner_id.id,
        )


class TestAddressAbstractImportMapper(AddressAbstractTestBase):

    def setUp(self):
        super(TestAddressAbstractImportMapper, self).setUp()
        self.Unit = address_abstract.CarepointAddressAbstractImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_get_partner_defaults(self):
        """ It should return proper vals dict """
        expect = {
            'type': 'delivery',
            'customer': True,
        }
        res = self.unit._get_partner_defaults(self.record)
        self.assertDictEqual(expect, res)

    def test_has_empty_address_empty(self):
        """ It should return True when address is empty """
        partner = self.new_partner()
        res = self.unit._has_empty_address(partner)
        self.assertTrue(res)

    def test_has_empty_address_full(self):
        """ It should return False when partner has address """
        partner = self.new_partner()
        partner.street = 'street'
        res = self.unit._has_empty_address(partner)
        self.assertFalse(res)

    def test_partner_id_empty(self):
        """ It should return partner when empty address """
        patient = self.new_patient()
        res = self.unit.partner_id(
            self.record, patient,
        )
        expect = {'partner_id': patient.commercial_partner_id.id}
        self.assertDictEqual(expect, res)

    def test_partner_id_full(self):
        """ It should return new partner when full address """
        patient = self.new_patient()
        patient.commercial_partner_id.street = 'street'
        res = self.unit.partner_id(
            self.record, patient,
        )
        self.assertNotEqual(
            patient.commercial_partner_id.id,
            res.get('partner_id'),
        )

    def test_address_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.address_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.carepoint.address'
            )

    def test_address_id_to_odoo(self):
        """ It should get Odoo record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.address_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['addr_id'],
            )

    def test_address_id_return(self):
        """ It should return formatted address_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.address_id(self.record)
            expect = self.unit.binder_for().to_odoo()
            self.assertDictEqual({'address_id': expect}, res)

    def test_res_model_and_id(self):
        """ It should return values dict for medical entity """
        entity = mock.MagicMock()
        expect = {
            'res_id': entity.id,
            'res_model': entity._name,
        }
        res = self.unit.res_model_and_id(None, entity)
        self.assertDictEqual(expect, res)


class TestAddressAbstractImporter(AddressAbstractTestBase):

    def setUp(self):
        super(TestAddressAbstractImporter, self).setUp()
        self.Unit = address_abstract.CarepointAddressAbstractImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['addr_id'],
                    'carepoint.carepoint.address',
                ),
            ])


class TestAddressAbstractExportMapper(AddressAbstractTestBase):

    def setUp(self):
        super(TestAddressAbstractExportMapper, self).setUp()
        self.Unit = address_abstract.CarepointAddressAbstractExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()

    def test_addr_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.addr_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.carepoint.address'
            )

    def test_addr_id_to_backend(self):
        """ It should get backend record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_backend.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.addr_id(self.record)
            self.unit.binder_for().to_backend.assert_called_once_with(
                self.record.address_id.id,
            )

    def test_addr_id_return(self):
        """ It should return formatted addr_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.addr_id(self.record)
            expect = self.unit.binder_for().to_backend()
            self.assertDictEqual({'addr_id': expect}, res)

    def test_static_defaults(self):
        """ It should return a dict of default values """
        self.assertIsInstance(
            self.unit.static_defaults(self.record),
            dict,
        )


class TestAddressAbstractExporter(AddressAbstractTestBase):

    def setUp(self):
        super(TestAddressAbstractExporter, self).setUp()
        self.Unit = address_abstract.CarepointAddressAbstractExporter
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()
        self.unit.binding_record = self.record

    def test_export_dependencies(self):
        """ It should export all dependencies """
        with mock.patch.object(self.unit, '_export_dependency') as mk:
            self.unit._export_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record.address_id,
                    'carepoint.carepoint.address',
                ),
            ])
