# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.connector_carepoint.unit import mapper

from .common import SetUpCarepointBase


class TestCarepointImporterMapper(SetUpCarepointBase):

    def setUp(self):
        super(TestCarepointImporterMapper, self).setUp()
        self.Importer = mapper.CarepointImportMapper
        self.model = 'carepoint.carepoint.store'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.importer = self.Importer(self.mock_env)

    def test_backend_id(self):
        """ It should map backend_id correctly """
        res = self.importer.backend_id(True)
        expect = {'backend_id': self.importer.backend_record.id}
        self.assertDictEqual(expect, res)

    def test_company_id(self):
        """ It should map company_id correctly """
        res = self.importer.company_id(True)
        expect = {'company_id': self.importer.backend_record.company_id.id}
        self.assertDictEqual(expect, res)
