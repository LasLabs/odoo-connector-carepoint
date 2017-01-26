# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.connector_carepoint.models import fdb_img

from ..common import SetUpCarepointBase


model = 'odoo.addons.connector_carepoint.models.fdb_img'


class EndTestException(Exception):
    pass


class FdbImgTestBase(SetUpCarepointBase):

    def setUp(self):
        super(FdbImgTestBase, self).setUp()
        self.model = 'carepoint.fdb.img'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'data': 'I am data'.encode('base64'),
            'IMGID': 123,
            'IMGFILENM': 'filename',
            'IMAGE_PATH': '/this/is/a/path.jpg',
        }


class TestFdbImgImportMapper(FdbImgTestBase):

    def setUp(self):
        super(TestFdbImgImportMapper, self).setUp()
        self.Unit = fdb_img.FdbImgImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['IMGID']}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_datas(self):
        """ It should return correct attribute """
        expect = {'datas': self.record['data']}
        res = self.unit.datas(self.record)
        self.assertDictEqual(expect, res)

    def test_mimetype(self):
        """ It should return correct attribute """
        expect = {'mimetype': 'image/jpeg'}
        res = self.unit.mimetype(self.record)
        self.assertDictEqual(expect, res)

    def test_type(self):
        """ It should return correct attribute """
        expect = {'type': 'binary'}
        res = self.unit.type(self.record)
        self.assertDictEqual(expect, res)


class TestFdbImgImporter(FdbImgTestBase):

    def setUp(self):
        super(TestFdbImgImporter, self).setUp()
        self.Unit = fdb_img.FdbImgImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_get_carepoint_data_read_image(self):
        """ It should obtain image from remote Carepoint server """
        with self.mock_adapter(self.unit):
            self.unit._get_carepoint_data()
            read = self.unit.backend_adapter.read_image
            read.assert_called_once_with(
                self.unit.backend_adapter.read()['IMAGE_PATH'],
            )

    def test_get_carepoint_data_return(self):
        """ It should return result of image read from server """
        with self.mock_adapter(self.unit):
            res = self.unit._get_carepoint_data()
            self.assertEqual(
                self.unit.backend_adapter.read_image(),
                res.data,
            )
