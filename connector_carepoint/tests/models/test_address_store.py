# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import address_store

from ...unit.backend_adapter import CarepointCRUDAdapter

from ..common import SetUpCarepointBase


_file = 'openerp.addons.connector_carepoint.models.address_store'


class EndTestException(Exception):
    pass


class AddressStoreTestBase(SetUpCarepointBase):

    def setUp(self):
        super(AddressStoreTestBase, self).setUp()
        self.model = 'carepoint.address.store'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'store_id': 1,
            'addr_id': 2,
        }


class TestAddressStoreImportMapper(AddressStoreTestBase):

    def setUp(self):
        super(TestAddressStoreImportMapper, self).setUp()
        self.Unit = address_store.CarepointAddressStoreImportMapper
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
                self.record['addr_id'],
            ),
        }
        self.assertDictEqual(expect, res)


class TestAddressStoreImporter(AddressStoreTestBase):

    def setUp(self):
        super(TestAddressStoreImporter, self).setUp()
        self.Unit = address_store.CarepointAddressStoreImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    @mock.patch('%s.CarepointAddressAbstractImporter' % _file,
                spec=address_store.CarepointAddressAbstractImporter,
                )
    def test_import_dependencies_super(self, _super):
        """ It should call the super """
        _super()._import_dependencies.side_effect = EndTestException
        with self.assertRaises(EndTestException):
            self.unit._import_dependencies()

    @mock.patch('%s.CarepointAddressAbstractImporter' % _file,
                spec=address_store.CarepointAddressAbstractImporter,
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


class TestCarepointAddressStoreUnit(AddressStoreTestBase):

    def setUp(self):
        super(TestCarepointAddressStoreUnit, self).setUp()
        self.Unit = address_store.CarepointAddressStoreUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_addresses_unit(self):
        """ It should get units for adapter and importer """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = [None, EndTestException]
            with self.assertRaises(EndTestException):
                self.unit._import_addresses(None, None)
            mk.assert_has_calls([
                mock.call(CarepointCRUDAdapter),
                mock.call(
                    address_store.CarepointAddressStoreImporter,
                ),
            ])

    def test_import_addresses_search(self):
        """ It should search adapter for filters """
        store = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._import_addresses(store, None)
            mk().search.assert_called_once_with(
                store_id=store,
            )

    def test_import_addresses_import(self):
        """ It should run importer on search results """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.return_value = [expect]
            self.unit._import_addresses(1, None)
            mk().run.assert_called_once_with(expect)
