# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import (
    sale_order_line
)

from ..common import SetUpCarepointBase


model = 'odoo.addons.connector_carepoint.models.%s' % (
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
            'rx_id': 1,
            'line_id': 2,
            'order_id': 3,
            'rxdisp_id': 4,
        }


class TestSaleOrderLineImportMapper(SaleOrderLineTestBase):

    def setUp(self):
        super(TestSaleOrderLineImportMapper, self).setUp()
        self.Unit = sale_order_line.SaleOrderLineImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['line_id']}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_tax_id(self):
        """ It should return tax Id as defined in backend defaults """
        expect = {
            'tax_id': [(4, self.unit.backend_record.default_sale_tax.id)]
        }
        res = self.unit.tax_id(self.record)
        self.assertDictEqual(expect, res)

    def test_price_unit(self):
        """ It should return correct attribute """
        expect = {'price_unit': 0}
        res = self.unit.price_unit(self.record)
        self.assertDictEqual(expect, res)

    def test_order_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.order_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.sale.order'
            )

    def test_order_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.order_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['order_id'],
            )

    def test_order_id_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit, 'binder_for'):
            order_id = self.unit.binder_for().to_odoo()
            expect = {'order_id': order_id}
            res = self.unit.order_id(self.record)
            self.assertDictEqual(expect, res)

    def test_prescription_data_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.prescription_data(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.rx.ord.ln'
            )

    def test_prescription_data_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.prescription_data(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['rx_id'], browse=True,
            )

    def test_prescription_data_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit, 'binder_for'):
            line_id = self.unit.binder_for().to_odoo()
            expect = {
                'prescription_order_line_id': line_id.id,
                'product_id': line_id.medicament_id.product_id.id,
                'product_uom': line_id.dispense_uom_id.id,
                'product_uom_qty': line_id.qty,
                'name': line_id.medicament_id.display_name,
            }
            res = self.unit.prescription_data(self.record)
            self.assertDictEqual(expect, res)


class TestSaleOrderLineUnit(SaleOrderLineTestBase):

    def setUp(self):
        super(TestSaleOrderLineUnit, self).setUp()
        self.Unit = sale_order_line.SaleOrderLineUnit
        self.unit = self.Unit(self.mock_env)

    def test_get_order_lines_unit_for(self):
        """ It should get unit for adapter """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._get_order_lines(True)
            mk.assert_called_once_with(
                sale_order_line.CarepointAdapter
            )

    def test_get_order_lines_search(self):
        """ It should get search adapter for order """
        expect = 'expect'
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._get_order_lines(expect)
            mk().search.assert_called_with(order_id=expect)

    def test_get_order_lines_return(self):
        """ It should return result of search operation """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            res = self.unit._get_order_lines(True)
            self.assertEqual(mk().search(), res)

    def test_import_sale_order_lines_unit_for(self):
        """ It should get unit for importer """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_sale_order_lines(True)
            mk.assert_called_once_with(
                sale_order_line.SaleOrderLineImporter
            )

    def tes_import_sale_order_lines_gets_lines(self):
        """ It should get lines associated to provided order """
        expect = 'expect'
        with mock.patch.object(self.unit, '_get_order_lines') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_sale_order_lines(expect)
            mk.assert_called_once_with(expect)

    def test_import_sale_order_lines_runs_importer_on_lines(self):
        """ It should run relevant importer for each line """
        expect = [mock.MagicMock()]
        with mock.patch.multiple(
            self.unit, _get_order_lines=mock.DEFAULT,
            unit_for=mock.DEFAULT,
        ) as mk:
            mk['_get_order_lines'].return_value = expect
            self.unit._import_sale_order_lines(True)
            mk['unit_for']().run.assert_called_once_with(expect[0])

    def test_get_order_line_count_gets_lines(self):
        """ It should get order lines for order """
        expect = 'expect'
        with mock.patch.object(self.unit, '_get_order_lines') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._get_order_line_count(expect)
            mk.assert_called_once_with(expect)

    def test_get_order_line_count_return(self):
        """ It should return length of lines """
        expect = ['expect', 'expect2']
        with mock.patch.object(self.unit, '_get_order_lines') as mk:
            mk.return_value = expect
            res = self.unit._get_order_line_count(True)
            self.assertEqual(len(expect), res)


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
                    self.record['rx_id'],
                    'carepoint.rx.ord.ln',
                ),
                mock.call(
                    self.record['order_id'],
                    'carepoint.sale.order',
                ),
            ])

    def test_after_import_depends(self):
        """ It should trigger reverse dependency chain after import """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            mk.side_effect = [None, EndTestException]
            with self.assertRaises(EndTestException):
                self.unit._after_import(True)
            mk.assert_has_calls([
                mock.call(
                    self.record['rxdisp_id'],
                    'carepoint.procurement.order',
                ),
                mock.call(
                    self.record['rxdisp_id'],
                    'carepoint.account.invoice.line',
                ),
            ])

    def test_after_import_unit_for(self):
        """ It should get unit for importer """
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT,
        ):
            self.unit.unit_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(True)
            self.unit.unit_for.assert_called_once_with(
                sale_order_line.ProcurementOrderUnit,
                model='carepoint.procurement.order',
            )

    def test_after_import_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT,
        ):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.procurement.order'
            )

    def test_after_import_to_backend(self):
        """ It should get backend for binder """
        expect = mock.MagicMock()
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT,
        ):
            self.unit.binder_for().to_backend.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(expect)
            self.unit.binder_for().to_backend.assert_called_once_with(
                expect.order_id
            )

    def test_after_import_get_order_line_cnt(self):
        """ It should get line count for the identified order """
        expect = mock.MagicMock()
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT,
        ):
            order_id = self.unit.binder_for().to_backend()
            line_cnt = self.unit.unit_for()._get_order_line_count
            line_cnt.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(expect)
            line_cnt.assert_called_once_with(order_id)

    def test_after_import_import_pickings(self):
        """ It should import pickings if all lines are imported """
        expect = mock.MagicMock()
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT,
        ):
            with mock.patch.object(self.unit, '_import_dependency') as depend:
                self.unit.binder_for().to_backend()
                self.unit.unit_for()._get_order_line_count.return_value = 1
                expect.order_id.order_line = [True]
                self.unit._after_import(expect)
                depend.assert_called_with(
                    self.record['order_id'], 'carepoint.stock.picking',
                )
