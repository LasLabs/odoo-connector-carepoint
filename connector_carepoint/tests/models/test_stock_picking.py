# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import (
    stock_picking
)

from ..common import SetUpCarepointBase


model = 'odoo.addons.connector_carepoint.models.%s' % (
    'stock_picking'
)


class EndTestException(Exception):
    pass


class StockPickingTestBase(SetUpCarepointBase):

    def setUp(self):
        super(StockPickingTestBase, self).setUp()
        self.model = 'carepoint.stock.picking'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'order_id': 1,
            'rx_id': 2,
        }


class TestStockPickingImportMapper(StockPickingTestBase):

    def setUp(self):
        super(TestStockPickingImportMapper, self).setUp()
        self.Unit = stock_picking.StockPickingImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['order_id']}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_odoo_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.odoo_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.sale.order'
            )

    def test_odoo_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.odoo_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['order_id'], browse=True,
            )

    def test_odoo_id_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit, 'binder_for'):
            order_id = self.unit.binder_for().to_odoo()
            expect = {'odoo_id': order_id.picking_ids[0].id}
            res = self.unit.odoo_id(self.record)
            self.assertDictEqual(expect, res)


class TestStockPickingUnit(StockPickingTestBase):

    def setUp(self):
        super(TestStockPickingUnit, self).setUp()
        self.Unit = stock_picking.StockPickingUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_pickings_for_sale_unit_for_adapter(self):
        """ It should get unit for adapter """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_pickings_for_sale(True)
            mk.assert_called_once_with(
                stock_picking.CarepointCRUDAdapter
            )

    def test_import_pickings_for_sale_unit_for_importer(self):
        """ It should get unit for importer """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = [None, EndTestException]
            with self.assertRaises(EndTestException):
                self.unit._import_pickings_for_sale(True)
            mk.assert_called_with(
                stock_picking.StockPickingImporter
            )

    def test_import_pickings_for_sale_search(self):
        """ It should get search adapter for order """
        expect = 'expect'
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_pickings_for_sale(expect)
            mk().search.assert_called_with(order_id=expect)

    def test_import_pickings_for_sale_run(self):
        """ It should iterate search result and run importer """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.return_value = [expect]
            self.unit._import_pickings_for_sale(True)
            mk().run.assert_called_once_with(
                expect
            )


class TestStockPickingImporter(StockPickingTestBase):

    def setUp(self):
        super(TestStockPickingImporter, self).setUp()
        self.Unit = stock_picking.\
            StockPickingImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['rx_id'],
                    'carepoint.rx.ord.ln',
                ),
                mock.call(
                    self.record['order_id'],
                    'carepoint.sale.order',
                ),
            ])

    def test_after_import_force_assign(self):
        """ It should force assign binding """
        expect = mock.MagicMock()
        expect.odoo_id.force_assign.side_effect = EndTestException
        with self.assertRaises(EndTestException):
            self.unit._after_import(expect)

    def test_after_import_create_transfer(self):
        """ It should create immediate transfer wizard w/ proper args """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit.session, 'env') as env:
            create = env['stock.immediate.transfer'].create
            create.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(expect)
            create.assert_called_once_with({
                'pick_id': expect.odoo_id.id,
            })

    def test_after_import_process_transfer(self):
        """ It should process the transfer wizard """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit.session, 'env') as env:
            create = env['stock.immediate.transfer'].create
            create.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(expect)
            create.assert_called_once_with({
                'pick_id': expect.odoo_id.id,
            })
