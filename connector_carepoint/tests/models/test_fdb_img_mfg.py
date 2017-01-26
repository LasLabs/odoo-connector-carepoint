# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import fdb_img_mfg

from ..common import SetUpCarepointBase


model = 'odoo.addons.connector_carepoint.models.fdb_img'


class EndTestException(Exception):
    pass


class FdbImgMfgTestBase(SetUpCarepointBase):

    def setUp(self):
        super(FdbImgMfgTestBase, self).setUp()
        self.model = 'carepoint.fdb.img.mfg'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'IMGMFGID': 123,
            'IMGMFGNAME': ' Image Name ',
        }


class TestFdbImgMfgImportMapper(FdbImgMfgTestBase):

    def setUp(self):
        super(TestFdbImgMfgImportMapper, self).setUp()
        self.Unit = fdb_img_mfg.FdbImgMfgImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['IMGMFGID']}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_manufacturer_id_search(self):
        """ It should search for manufacturer w/ proper args """
        with mock.patch.object(self.unit.session, 'env') as env:
            self.unit.manufacturer_id(self.record)
            env[''].search.assert_called_once_with(
                [('name', 'ilike', self.record['IMGMFGNAME'].strip())],
                limit=1,
            )

    def test_manufacturer_id_return(self):
        """ It should return result of search if any """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit.session, 'env') as env:
            env[''].search.return_value = [expect]
            res = self.unit.manufacturer_id(self.record)
            self.assertDictEqual(
                {'manufacturer_id': expect.id},
                res,
            )
