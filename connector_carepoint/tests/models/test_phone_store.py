# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import phone_store

from ...unit.backend_adapter import CarepointCRUDAdapter

from ..common import SetUpCarepointBase


_file = 'openerp.addons.connector_carepoint.models.phone_store'


class EndTestException(Exception):
    pass


class PhoneStoreTestBase(SetUpCarepointBase):

    def setUp(self):
        super(PhoneStoreTestBase, self).setUp()
        self.model = 'carepoint.phone.store'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'store_id': 1,
            'phone_id': 2,
        }


class TestPhoneStoreImportMapper(PhoneStoreTestBase):

    def setUp(self):
        super(TestPhoneStoreImportMapper, self).setUp()
        self.Unit = phone_store.CarepointPhoneStoreImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_partner_id_get_binder(self):
        """ It should get binder for store """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.carepoint.store'
            )

    def test_partner_id_to_odoo(self):
        """ It should get Odoo record for store """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['store_id'], browse=True,
            )

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {
            'carepoint_id': '%d,%d' % (
                self.record['store_id'],
                self.record['phone_id'],
            ),
        }
        self.assertDictEqual(expect, res)


class TestPhoneStoreImporter(PhoneStoreTestBase):

    def setUp(self):
        super(TestPhoneStoreImporter, self).setUp()
        self.Unit = phone_store.CarepointPhoneStoreImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    @mock.patch('%s.CarepointPhoneAbstractImporter' % _file,
                spec=phone_store.CarepointPhoneAbstractImporter,
                )
    def test_import_dependencies_super(self, _super):
        """ It should call the super """
        _super()._import_dependencies.side_effect = EndTestException
        with self.assertRaises(EndTestException):
            self.unit._import_dependencies()

    @mock.patch('%s.CarepointPhoneAbstractImporter' % _file,
                spec=phone_store.CarepointPhoneAbstractImporter,
                )
    def test_import_dependencies_super(self, _super):
        """ It should import all dependencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['store_id'],
                    'carepoint.carepoint.store',
                ),
            ])


class TestCarepointPhoneStoreUnit(PhoneStoreTestBase):

    def setUp(self):
        super(TestCarepointPhoneStoreUnit, self).setUp()
        self.Unit = phone_store.CarepointPhoneStoreUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_phones_unit(self):
        """ It should get units for adapter and importer """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = [None, EndTestException]
            with self.assertRaises(EndTestException):
                self.unit._import_phones(None, None)
            mk.assert_has_calls([
                mock.call(CarepointCRUDAdapter),
                mock.call(
                    phone_store.CarepointPhoneStoreImporter,
                ),
            ])

    def test_import_phones_search(self):
        """ It should search adapter for filters """
        store = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._import_phones(store, None)
            mk().search.assert_called_once_with(
                store_id=store,
            )

    def test_import_phones_import(self):
        """ It should run importer on search results """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.return_value = [expect]
            self.unit._import_phones(1, None)
            mk().run.assert_called_once_with(expect)
