# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import address_patient

from ...unit.backend_adapter import CarepointCRUDAdapter

from ..common import SetUpCarepointBase


_file = 'openerp.addons.connector_carepoint.models.address_patient'


class EndTestException(Exception):
    pass


class AddressPatientTestBase(SetUpCarepointBase):

    def setUp(self):
        super(AddressPatientTestBase, self).setUp()
        self.model = 'carepoint.address.patient'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'pat_id': 1,
            'addr_id': 2,
        }


class TestAddressPatientImportMapper(AddressPatientTestBase):

    def setUp(self):
        super(TestAddressPatientImportMapper, self).setUp()
        self.Unit = address_patient.CarepointAddressPatientImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_partner_id_get_binder(self):
        """ It should get binder for patient """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.patient'
            )

    def test_partner_id_to_odoo(self):
        """ It should get Odoo record for patient """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['pat_id'], browse=True,
            )

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {
            'carepoint_id': '%d,%d' % (
                self.record['pat_id'],
                self.record['addr_id'],
            ),
        }
        self.assertDictEqual(expect, res)


class TestAddressPatientImporter(AddressPatientTestBase):

    def setUp(self):
        super(TestAddressPatientImporter, self).setUp()
        self.Unit = address_patient.CarepointAddressPatientImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    @mock.patch('%s.CarepointAddressAbstractImporter' % _file,
                spec=address_patient.CarepointAddressAbstractImporter,
                )
    def test_import_dependencies_import(self, _super):
        """ It should import all dependencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['pat_id'],
                    'carepoint.medical.patient',
                ),
            ])


class TestCarepointAddressPatientUnit(AddressPatientTestBase):

    def setUp(self):
        super(TestCarepointAddressPatientUnit, self).setUp()
        self.Unit = address_patient.CarepointAddressPatientUnit
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
                    address_patient.CarepointAddressPatientImporter,
                ),
            ])

    def test_import_addresses_search(self):
        """ It should search adapter for filters """
        patient = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._import_addresses(patient, None)
            mk().search.assert_called_once_with(
                pat_id=patient,
            )

    def test_import_addresses_import(self):
        """ It should run importer on search results """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.return_value = [expect]
            self.unit._import_addresses(1, None)
            mk().run.assert_called_once_with(expect)


class TestAddressPatientExportMapper(AddressPatientTestBase):

    def setUp(self):
        super(TestAddressPatientExportMapper, self).setUp()
        self.Unit = address_patient.CarepointAddressPatientExportMapper
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
                self.record.res_id,
            )

    def test_pat_id_return(self):
        """ It should return formatted pat_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.pat_id(self.record)
            expect = self.unit.binder_for().to_backend()
            self.assertDictEqual({'pat_id': expect}, res)
