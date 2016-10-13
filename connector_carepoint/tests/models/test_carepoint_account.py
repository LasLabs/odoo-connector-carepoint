# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import carepoint_account

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class AccountTestBase(SetUpCarepointBase):

    def setUp(self):
        super(AccountTestBase, self).setUp()
        self.model = 'carepoint.account'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'pat_id': 123,
            'ID': 9,
        }

    def new_partner(self):
        return self.env['res.partner'].create({'name': 'Partner'})

    def new_patient(self, partner=None):
        if not partner:
            partner = self.new_partner()
        return self.env['medical.patient'].create({
            'partner_id': partner.id,
        })


class TestCarepointAccount(AccountTestBase):

    def setUp(self):
        super(TestCarepointAccount, self).setUp()
        self.model = self.env['carepoint.account']

    def new_patient_account(self):
        self.patient = self.new_patient()
        return self.model.create({
            'patient_id': self.patient.id,
        })

    def test_get_by_patient_existing_account(self):
        """ It should return patient associated with existing account """
        account = self.new_patient_account()
        res = account._get_by_patient(account.patient_id, False, False)
        self.assertEqual(account, res)

    def test_get_by_patient_create(self):
        """ It should create new account when non-exist and create """
        patient = self.new_patient()
        res = self.model._get_by_patient(patient, True, False)
        self.assertEqual(patient, res.patient_id)

    def test_get_by_patient_recurse(self):
        """ It should recurse into children when create and recurse """
        parent, child = self.new_patient(), self.new_patient()
        child.parent_id = parent.partner_id.id
        self.model._get_by_patient(parent, True, True)
        account = self.model.search(
            [('patient_id', '=', child.id)]
        )
        self.assertTrue(len(account))


class TestAccountImportMapper(AccountTestBase):

    def setUp(self):
        super(TestAccountImportMapper, self).setUp()
        self.Unit = carepoint_account.CarepointAccountImportMapper
        self.unit = self.Unit(self.mock_env)

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

    def test_carepoint_id(self):
        """ It should return proper values dict """
        expect = '%s,%s' % (self.record['pat_id'], self.record['ID'])
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(
            {'carepoint_id': expect},
            res,
        )


class TestAccountImporter(AccountTestBase):

    def setUp(self):
        super(TestAccountImporter, self).setUp()
        self.Unit = carepoint_account.CarepointAccountImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['pat_id'],
                    'carepoint.medical.patient',
                ),
            ])


class TestAccountExportMapper(AccountTestBase):

    def setUp(self):
        super(TestAccountExportMapper, self).setUp()
        self.Unit = carepoint_account.CarepointAccountExportMapper
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
                self.record.patient_id,
            )

    def test_pat_id_return(self):
        """ It should return formatted pat_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.pat_id(self.record)
            expect = self.unit.binder_for().to_backend()
            self.assertDictEqual({'pat_id': expect}, res)

    def test_static_defaults(self):
        """ It should return a dict of default values """
        self.assertIsInstance(
            self.unit.static_defaults(self.record),
            dict,
        )


class TestAccountExporter(AccountTestBase):

    def setUp(self):
        super(TestAccountExporter, self).setUp()
        self.Unit = carepoint_account.CarepointAccountExporter
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()
        self.unit.binding_record = self.record

    def test_export_dependencies(self):
        """ It should export all dependencies """
        with mock.patch.object(self.unit, '_export_dependency') as mk:
            self.unit._export_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record.patient_id,
                    'carepoint.medical.patient',
                ),
            ])
