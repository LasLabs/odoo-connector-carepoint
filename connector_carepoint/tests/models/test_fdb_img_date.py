# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import (
    fdb_img_date
)

from ..common import SetUpCarepointBase


model = 'openerp.addons.connector_carepoint.models.%s' % (
    'fdb_img_date'
)


class EndTestException(Exception):
    pass


class FdbImgDateTestBase(SetUpCarepointBase):

    def setUp(self):
        super(FdbImgDateTestBase, self).setUp()
        self.model = 'carepoint.fdb.img.date'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'IMGUNIQID': 1,
            'IMGID': 2,
            'IMGSTRTDT': '2016-01-01',
        }


class TestFdbImgDateImportMapper(FdbImgDateTestBase):

    def setUp(self):
        super(TestFdbImgDateImportMapper, self).setUp()
        self.Unit = fdb_img_date.FdbImgDateImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': '%s,%s' % (self.record['IMGUNIQID'],
                                             self.record['IMGSTRTDT'],
                                             )}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_image_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.image_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.fdb.img'
            )

    def test_image_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.image_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['IMGID'],
            )

    def test_image_id_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit, 'binder_for'):
            image_id = self.unit.binder_for().to_odoo()
            expect = {'image_id': image_id}
            res = self.unit.image_id(self.record)
            self.assertDictEqual(expect, res)

    def test_relation_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.relation_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.fdb.img.id'
            )

    def test_relation_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.relation_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['IMGUNIQID'],
            )

    def test_relation_id_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit, 'binder_for'):
            relation_id = self.unit.binder_for().to_odoo()
            expect = {'relation_id': relation_id}
            res = self.unit.relation_id(self.record)
            self.assertDictEqual(expect, res)


class TestFdbImgDateUnit(FdbImgDateTestBase):

    def setUp(self):
        super(TestFdbImgDateUnit, self).setUp()
        self.Unit = fdb_img_date.FdbImgDateUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_by_unique_id_unit_for(self):
        """ It should get unit for adapter """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            self.unit._import_by_unique_id(True)
            mk.assert_has_calls([
                mock.call(fdb_img_date.FdbImgDateAdapter),
                mock.call(fdb_img_date.FdbImgDateImporter),
            ])

    def test_import_by_unique_id_search(self):
        """ It should search for appropriate records """
        expect = 'expect'
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_by_unique_id(expect)
            mk().search.assert_called_with(IMGUNIQID=expect)

    def test_import_by_unique_id_import(self):
        """ It should import the records """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.return_value = [expect]
            self.unit._import_by_unique_id(True)
            mk().run.assert_called_once_with(expect)


class TestFdbImgDateImporter(FdbImgDateTestBase):

    def setUp(self):
        super(TestFdbImgDateImporter, self).setUp()
        self.Unit = fdb_img_date.\
            FdbImgDateImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['IMGUNIQID'],
                    'carepoint.fdb.img.id',
                ),
                mock.call(
                    self.record['IMGID'],
                    'carepoint.fdb.img',
                ),
            ])
