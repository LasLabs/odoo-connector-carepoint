# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import (
    sale_order
)

from ..common import SetUpCarepointBase


model = 'odoo.addons.connector_carepoint.models.%s' % (
    'sale_order'
)


class EndTestException(Exception):
    pass


class SaleOrderTestBase(SetUpCarepointBase):

    def setUp(self):
        super(SaleOrderTestBase, self).setUp()
        self.model = 'carepoint.sale.order'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'invoice_nbr': 1,
            'submit_date': '2016-01-23 01:23:45',
            'add_date': '2016-10-32 10:32:54',
            'acct_id': 2,
            'store_id': 3,
            'order_state_cn': 4,
            'order_id': 5,
        }


class TestSaleOrderImportMapper(SaleOrderTestBase):

    def setUp(self):
        super(TestSaleOrderImportMapper, self).setUp()
        self.Unit = sale_order.SaleOrderImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['order_id']}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_name(self):
        """ It should return properly formatted name """
        expect = '{prefix}{name}'.format(
            prefix=self.unit.backend_record.sale_prefix,
            name=self.record['invoice_nbr'],
        )
        expect = {'name': expect}
        res = self.unit.name(self.record)
        self.assertDictEqual(expect, res)

    def test_date_order_submit(self):
        """ It should return submit date if existing """
        expect = {'date_order': self.record['submit_date']}
        res = self.unit.date_order(self.record)
        self.assertDictEqual(expect, res)

    def test_date_order_add(self):
        """ It should return add date if no submit date """
        record = self.record
        record['submit_date'] = False
        expect = {'date_order': record['add_date']}
        res = self.unit.date_order(record)
        self.assertDictEqual(expect, res)

    def test_pharmacy_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.pharmacy_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.carepoint.store'
            )

    def test_pharmacy_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.pharmacy_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['store_id'],
            )

    def test_pharmacy_id_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit, 'binder_for'):
            store_id = self.unit.binder_for().to_odoo()
            expect = {'pharmacy_id': store_id}
            res = self.unit.pharmacy_id(self.record)
            self.assertDictEqual(expect, res)

    def test_partner_data_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_data(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.carepoint.account'
            )

    def test_partner_data_acct_to_odoo(self):
        """ It should get Odoo record for binding if acct_id is defined """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.partner_data(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['acct_id'], browse=True,
            )

    def test_partner_data_acct_return(self):
        """ It should return proper vals dict if acct_id is defined """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.partner_data(self.record)
            partner_id = self.unit.binder_for().to_odoo().\
                patient_id.commercial_partner_id
            expect = {
                'partner_id': partner_id.id,
                'payment_term_id': partner_id.property_payment_term_id.id,
            }
            self.assertDictEqual(expect, res)

    def test_partner_data_null_ref(self):
        """ It should get null patient if no account defined """
        with mock.patch.object(self.unit, 'binder_for'):
            with mock.patch.object(self.unit.session, 'env') as env:
                env.ref.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    self.unit.partner_data({'acct_id': False})
                env.ref.assert_called_once_with(
                    'connector_carepoint.patient_null'
                )

    def test_partner_data_null_return(self):
        """ It should return proper vals dict if no account defined """
        with mock.patch.object(self.unit, 'binder_for'):
            with mock.patch.object(self.unit.session, 'env') as env:
                res = self.unit.partner_data({'acct_id': False})
                partner_id = env.ref().commercial_partner_id
                expect = {
                    'partner_id': partner_id.id,
                    'payment_term_id': partner_id.property_payment_term_id.id,
                }
                self.assertDictEqual(expect, res)

    def test_state_call(self):
        """ It should locate correct state ref """
        with mock.patch.object(self.unit.session, 'env') as env:
            env.ref.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.state(self.record)
            env.ref.assert_called_once_with(
                'connector_carepoint.state_%d' % self.record['order_state_cn']
            )

    def test_state_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit.session, 'env') as env:
            res = self.unit.state(self.record)
            expect = {'state': env.ref().order_state}
            self.assertDictEqual(expect, res)


class TestSaleOrderImporter(SaleOrderTestBase):

    def setUp(self):
        super(TestSaleOrderImporter, self).setUp()
        self.Unit = sale_order.SaleOrderImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['acct_id'],
                    'carepoint.carepoint.account',
                ),
            ])

    def test_after_import(self):
        """ This is a useless test, but coveralls disagrees """
        res = self.unit._after_import(True)
        self.assertEqual(None, res)
