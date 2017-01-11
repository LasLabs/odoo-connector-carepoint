# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import address_organization

from ...unit.backend_adapter import CarepointCRUDAdapter

from ..common import SetUpCarepointBase


_file = 'odoo.addons.connector_carepoint.models.address_organization'


class EndTestException(Exception):
    pass


class AddressOrganizationTestBase(SetUpCarepointBase):

    def setUp(self):
        super(AddressOrganizationTestBase, self).setUp()
        self.model = 'carepoint.address.organization'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'org_id': 1,
            'addr_id': 2,
        }


class TestAddressOrganizationImportMapper(AddressOrganizationTestBase):

    def setUp(self):
        super(TestAddressOrganizationImportMapper, self).setUp()
        self.Unit = \
            address_organization.CarepointAddressOrganizationImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_partner_id_get_binder(self):
        """ It should get binder for organization """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.organization'
            )

    def test_partner_id_to_odoo(self):
        """ It should get Odoo record for organization """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['org_id'], browse=True,
            )

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {
            'carepoint_id': '%d,%d' % (
                self.record['org_id'],
                self.record['addr_id'],
            ),
        }
        self.assertDictEqual(expect, res)


class TestAddressOrganizationImporter(AddressOrganizationTestBase):

    def setUp(self):
        super(TestAddressOrganizationImporter, self).setUp()
        self.Unit = address_organization.CarepointAddressOrganizationImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies_import(self):
        """ It should import all dependencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['org_id'],
                    'carepoint.medical.organization',
                ),
            ])


class TestCarepointAddressOrganizationUnit(AddressOrganizationTestBase):

    def setUp(self):
        super(TestCarepointAddressOrganizationUnit, self).setUp()
        self.Unit = address_organization.CarepointAddressOrganizationUnit
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
                    address_organization.CarepointAddressOrganizationImporter,
                ),
            ])

    def test_import_addresses_search(self):
        """ It should search adapter for filters """
        organization = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._import_addresses(organization, None)
            mk().search.assert_called_once_with(
                org_id=organization,
            )

    def test_import_addresses_import(self):
        """ It should run importer on search results """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.return_value = [expect]
            self.unit._import_addresses(1, None)
            mk().run.assert_called_once_with(expect)


class TestAddressOrganizationExportMapper(AddressOrganizationTestBase):

    def setUp(self):
        super(TestAddressOrganizationExportMapper, self).setUp()
        self.Unit = \
            address_organization.CarepointAddressOrganizationExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()

    def test_org_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.org_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.org.bind'
            )

    def test_org_id_to_backend(self):
        """ It should get backend record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_backend.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.org_id(self.record)
            self.unit.binder_for().to_backend.assert_called_once_with(
                self.record.res_id,
            )

    def test_org_id_return(self):
        """ It should return formatted org_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.org_id(self.record)
            expect = self.unit.binder_for().to_backend()
            self.assertDictEqual({'org_id': expect}, res)
