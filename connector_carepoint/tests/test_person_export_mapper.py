# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.connector_carepoint.unit import mapper

from .common import SetUpCarepointBase


class TestPersonExportMapper(SetUpCarepointBase):

    def setUp(self):
        super(TestPersonExportMapper, self).setUp()
        self.Exporter = mapper.PersonExportMapper
        self.model = 'carepoint.medical.patient'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.exporter = self.Exporter(self.mock_env)
        self.record = self.env[self.model].create({
            'name': 'Test Mc Testerface',
        })

    def test_names_full(self):
        """ It should correctly parse full name w/ spaces into pieces """
        res = self.exporter.names(self.record)
        expect = {'fname': 'Test',
                  'lname': 'Mc Testerface',
                  }
        self.assertDictEqual(expect, res)

    def test_name_no_first(self):
        """ It should properly handle no first name """
        record = self.env[self.model].create({'name': 'Lname'})
        res = self.exporter.names(record)
        expect = {'fname': '-',
                  'lname': 'Lname',
                  }
        self.assertDictEqual(expect, res)
