# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import (
    fdb_img_id
)

from ..common import SetUpCarepointBase


model = 'odoo.addons.connector_carepoint.models.%s' % (
    'fdb_img_id'
)


class EndTestException(Exception):
    pass


class FdbImgIdTestBase(SetUpCarepointBase):

    def setUp(self):
        super(FdbImgIdTestBase, self).setUp()
        self.model = 'carepoint.fdb.img.id'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'IMGUNIQID': 1,
            'IMGMFGID': 2,
            'IMGNDC': ' ndc ',
        }


class TestFdbImgIdImportMapper(FdbImgIdTestBase):

    def setUp(self):
        super(TestFdbImgIdImportMapper, self).setUp()
        self.Unit = fdb_img_id.FdbImgIdImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['IMGUNIQID']}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_ndc_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.ndc_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.fdb.ndc'
            )

    def test_ndc_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.ndc_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['IMGNDC'].strip(),
            )

    def test_ndc_id_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit, 'binder_for'):
            ndc_id = self.unit.binder_for().to_odoo()
            expect = {'ndc_id': ndc_id}
            res = self.unit.ndc_id(self.record)
            self.assertDictEqual(expect, res)

    def test_manufacturer_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.manufacturer_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.fdb.img.mfg'
            )

    def test_manufacturer_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.manufacturer_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['IMGMFGID'],
            )

    def test_manufacturer_id_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit, 'binder_for'):
            manufacturer_id = self.unit.binder_for().to_odoo()
            expect = {'manufacturer_id': manufacturer_id}
            res = self.unit.manufacturer_id(self.record)
            self.assertDictEqual(expect, res)


class TestFdbImgIdUnit(FdbImgIdTestBase):

    def setUp(self):
        super(TestFdbImgIdUnit, self).setUp()
        self.Unit = fdb_img_id.FdbImgIdUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_by_ndc_unit_for(self):
        """ It should get unit for adapter """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._import_by_ndc(True)
            mk.assert_has_calls([
                mock.call(fdb_img_id.FdbImgIdAdapter),
                mock.call(fdb_img_id.FdbImgIdImporter),
            ])

    def test_import_by_ndc_search(self):
        """ It should search for appropriate records """
        expect = 'expect'
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_by_ndc(expect)
            mk().search.assert_called_with(IMGNDC=expect)

    def test_import_by_ndc_import(self):
        """ It should import the records """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.return_value = [expect]
            self.unit._import_by_ndc(True)
            mk().run.assert_called_once_with(expect)


class TestFdbImgIdImporter(FdbImgIdTestBase):

    def setUp(self):
        super(TestFdbImgIdImporter, self).setUp()
        self.Unit = fdb_img_id.\
            FdbImgIdImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['IMGNDC'].strip(),
                    'carepoint.fdb.ndc',
                ),
                mock.call(
                    self.record['IMGMFGID'],
                    'carepoint.fdb.img.mfg',
                ),
            ])

    def test_after_import_unit(self):
        """ It should get proper unit """
        with mock.patch.object(self.unit, 'unit_for'):
            self.unit._after_import(None)
            self.unit.unit_for.assert_called_once_with(
                fdb_img_id.FdbImgDateUnit,
                model='carepoint.fdb.img.date',
            )

    def test_after_import_import(self):
        """ It should run import method on unit """
        with mock.patch.object(self.unit, 'unit_for'):
            self.unit._after_import(None)
            self.unit.unit_for()._import_by_unique_id.assert_called_once_with(
                self.record['IMGUNIQID'],
            )
