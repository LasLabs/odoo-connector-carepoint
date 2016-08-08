# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import (
    sale_order_line
)

from ..common import SetUpCarepointBase


model = 'openerp.addons.connector_carepoint.models.%s' % (
    'sale_order_line'
)


class EndTestException(Exception):
    pass


class SaleOrderLineTestBase(SetUpCarepointBase):

    def setUp(self):
        super(SaleOrderLineTestBase, self).setUp()
        self.model = 'carepoint.sale.order.line'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'gcn_seqno': 1,
            'pemono': 2,
            'pemono_sn': 3,
        }


class TestSaleOrderLineImportMapper(SaleOrderLineTestBase):

    def setUp(self):
        super(TestSaleOrderLineImportMapper, self).setUp()
        self.Unit = sale_order_line.SaleOrderLineImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['gcn_seqno']}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_gcn_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.gcn_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.fdb.gcn'
            )

    def test_gcn_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.gcn_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['gcn_seqno'],
            )

    def test_gcn_id_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit, 'binder_for'):
            gcn_id = self.unit.binder_for().to_odoo()
            expect = {'gcn_id': gcn_id}
            res = self.unit.gcn_id(self.record)
            self.assertDictEqual(expect, res)


class TestSaleOrderLineImporter(SaleOrderLineTestBase):

    def setUp(self):
        super(TestSaleOrderLineImporter, self).setUp()
        self.Unit = sale_order_line.\
            SaleOrderLineImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['gcn_seqno'],
                    'carepoint.fdb.gcn',
                ),
            ])
