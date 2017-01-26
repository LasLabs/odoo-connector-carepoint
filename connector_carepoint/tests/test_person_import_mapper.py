# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.connector_carepoint.unit import mapper

from .common import SetUpCarepointBase


class TestPersonImporterMapper(SetUpCarepointBase):

    def setUp(self):
        super(TestPersonImporterMapper, self).setUp()
        self.Importer = mapper.PersonImportMapper
        self.model = 'carepoint.medical.patient'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.importer = self.Importer(self.mock_env)
        self.record = {
            'fname': 'dave',
            'lname': 'lasley',
        }

    def test_name_full(self):
        """ It should correctly handle all name parts combined """
        res = self.importer.name(self.record)
        expect = '%s %s' % (self.record['fname'].title(),
                            self.record['lname'].title())
        expect = {'name': expect}
        self.assertDictEqual(expect, res)

    def test_name_first(self):
        """ It should correctly handle only first name present """
        del self.record['lname']
        res = self.importer.name(self.record)
        expect = {'name': self.record['fname'].title()}
        self.assertDictEqual(expect, res)

    def test_name_last(self):
        """ It should correctly handle only last name present """
        del self.record['fname']
        res = self.importer.name(self.record)
        expect = {'name': self.record['lname'].title()}
        self.assertDictEqual(expect, res)
