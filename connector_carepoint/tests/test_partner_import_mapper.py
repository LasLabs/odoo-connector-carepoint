# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.connector_carepoint.unit import mapper

from .common import SetUpCarepointBase


class TestPartnerImportMapper(SetUpCarepointBase):

    def setUp(self):
        super(TestPartnerImportMapper, self).setUp()
        self.Importer = mapper.PartnerImportMapper
        self.model = 'carepoint.medical.patient'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.importer = self.Importer(self.mock_env)

    def test_tz(self):
        """ It should return default_tz as defined on backend """
        res = self.importer.tz(True)
        expect = {'tz': self.importer.backend_record.default_tz}
        self.assertDictEqual(expect, res)

    def test_currency_id(self):
        """ It should return the same currency as the backend's company """
        res = self.importer.currency_id(True)
        expect = {
            'currency_id':
                self.importer.backend_record.company_id.currency_id.id,
        }
        self.assertDictEqual(expect, res)

    def test_property_payment_term_id(self):
        """ It should return the proper default as defined on backend """
        res = self.importer.property_payment_term_id(True)
        expect = {
            'property_payment_term_id':
                self.importer.backend_record.
                default_customer_payment_term_id.id,
        }
        self.assertDictEqual(expect, res)

    def test_property_account_payable_id(self):
        """ It should return the proper default as defined on backend """
        res = self.importer.property_account_payable_id(True)
        expect = {
            'property_account_payable_id':
                self.importer.backend_record.default_account_payable_id.id,
        }
        self.assertDictEqual(expect, res)

    def test_property_supplier_payment_term_id(self):
        """ It should return the proper default as defined on backend """
        res = self.importer.property_supplier_payment_term_id(True)
        expect = {
            'property_supplier_payment_term_id':
                self.importer.backend_record.
                default_supplier_payment_term_id.id,
        }
        self.assertDictEqual(expect, res)

    def test_property_account_receivable_id(self):
        """ It should return the proper default as defined on backend """
        res = self.importer.property_account_receivable_id(True)
        expect = {
            'property_account_receivable_id':
                self.importer.backend_record.
                default_account_receivable_id.id,
        }
        self.assertDictEqual(expect, res)
