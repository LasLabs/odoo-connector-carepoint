# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import carepoint_organization

from ..common import SetUpCarepointBase

from ...models.carepoint_organization import CarepointAddressOrganizationUnit


class EndTestException(Exception):
    pass


class CarepointOrganizationTestBase(SetUpCarepointBase):

    def setUp(self):
        super(CarepointOrganizationTestBase, self).setUp()
        self.model = 'carepoint.org.bind'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'name': 'Test Pharmacy',
            'org_id': 123,
        }


class TestCarepointOrganizationImportMapper(CarepointOrganizationTestBase):

    def setUp(self):
        super(TestCarepointOrganizationImportMapper, self).setUp()
        self.Unit = carepoint_organization.CarepointOrganizationImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_odoo_id_organization(self):
        """ It should return odoo_id of pharmacies with same name """
        expect = self.env['carepoint.organization'].create(
            self.record
        )
        res = self.unit.odoo_id(self.record)
        expect = {'odoo_id': expect.id}
        self.assertDictEqual(expect, res)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {'carepoint_id': self.record['org_id']}
        self.assertDictEqual(expect, res)


class TestCarepointOrganizationImporter(CarepointOrganizationTestBase):

    def setUp(self):
        super(TestCarepointOrganizationImporter, self).setUp()
        self.Unit = carepoint_organization.CarepointOrganizationImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_id = 9876
        self.unit.carepoint_record = self.record

    def test_after_import_unit(self):
        """ It should get unit for importer """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._after_import(None)
            mk.assert_called_once_with(
                CarepointAddressOrganizationUnit,
                model='carepoint.carepoint.address.organization',
            )

    def test_after_import_import_addresses(self):
        """ It should call import_addresses on unit w/ proper args """
        expect = 'partner'
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._after_import(expect)
            mk()._import_addresses.assert_called_once_with(
                self.unit.carepoint_id,
                expect,
            )


class TestCarepointOrganizationExportMapper(CarepointOrganizationTestBase):

    def setUp(self):
        super(TestCarepointOrganizationExportMapper, self).setUp()
        self.Unit = carepoint_organization.CarepointOrganizationExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()

    def test_addr_id(self):
        """ It should return proper vals dict """
        res = self.unit.addr_id(self.record)
        self.assertDictEqual(
            {'org_id': self.record.carepoint_id},
            res,
        )


class TestCarepointOrganizationExporter(CarepointOrganizationTestBase):

    def setUp(self):
        super(TestCarepointOrganizationExporter, self).setUp()
        self.Unit = carepoint_organization.CarepointOrganizationExporter
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
