# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import procurement_order

from ..common import SetUpCarepointBase


model = 'openerp.addons.connector_carepoint.models.procurement_order'


class EndTestException(Exception):
    pass


class ProcurementOrderTestBase(SetUpCarepointBase):

    def setUp(self):
        super(ProcurementOrderTestBase, self).setUp()
        self.model = 'carepoint.procurement.order'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'rx_id': 'RxId12345',
            'order_id': 1234,
            'disp_ndc': ' 3r34234234e34tdf ',
            'dispense_qty': 987,
            'rxdisp_id': 123456789,
        }


class TestProcurementOrderUnit(ProcurementOrderTestBase):

    def setUp(self):
        super(TestProcurementOrderUnit, self).setUp()
        self.Unit = procurement_order.ProcurementOrderUnit
        self.unit = self.Unit(self.mock_env)

    def test_get_order_lines_unit_for(self):
        """ It should get unit for adapter """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._get_order_lines(True)
            mk.assert_called_once_with(
                procurement_order.CarepointCRUDAdapter
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

    def test_import_procurements_for_sale_unit_for(self):
        """ It should get unit for importer """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_procurements_for_sale(True)
            mk.assert_called_once_with(
                procurement_order.ProcurementOrderImporter
            )

    def test_import_procurements_for_sale_gets_lines(self):
        """ It should get lines associated to provided order """
        expect = 'expect'
        with mock.patch.object(self.unit, '_get_order_lines') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_procurements_for_sale(expect)
            mk.assert_called_once_with(expect)

    def test_import_procurements_for_sale_runs_importer_on_lines(self):
        """ It should run relevant importer for each line """
        expect = [mock.MagicMock()]
        with mock.patch.multiple(
            self.unit, _get_order_lines=mock.DEFAULT,
            unit_for=mock.DEFAULT,
        ) as mk:
            mk['_get_order_lines'].return_value = expect
            self.unit._import_procurements_for_sale(True)
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


class TestProcurementOrderImportMapper(ProcurementOrderTestBase):

    def setUp(self):
        super(TestProcurementOrderImportMapper, self).setUp()
        self.Unit = procurement_order.ProcurementOrderImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['rxdisp_id']}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_name_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.name(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.medical.prescription.order.line'
            )

    def test_name_to_odoo(self):
        """ It should get Odoo record for rx """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.name(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['rx_id'], browse=True,
            )

    def test_name_return(self):
        """ It should return formatted name """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.name(self.record)
            expect = 'RX %s - %s' % (
                self.record['rx_id'],
                self.unit.binder_for().to_odoo().medicament_id.display_name,
            )
            self.assertDictEqual({'name': expect}, res)

    def test_order_line_procurement_data_rx_line_binder(self):
        """ It should get binder for model """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.order_line_procurement_data(self.record)
            self.unit.binder_for.assert_called_with(
                'carepoint.medical.prescription.order.line'
            )

    def test_order_line_procurement_data_rx_line_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.order_line_procurement_data(self.record)
            self.unit.binder_for().to_odoo.assert_called_with(
                self.record['rx_id'], browse=True,
            )

    def test_order_line_procurement_data_sale_order_binder(self):
        """ It should get binder for model """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = [mock.MagicMock(),
                                                EndTestException]
            with self.assertRaises(EndTestException):
                self.unit.order_line_procurement_data(self.record)
            self.unit.binder_for.assert_called_with(
                'carepoint.sale.order'
            )

    def test_order_line_procurement_data_sale_order_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = [mock.MagicMock(),
                                                          EndTestException]
            with self.assertRaises(EndTestException):
                self.unit.order_line_procurement_data(self.record)
            self.unit.binder_for().to_odoo.assert_called_with(
                self.record['order_id'], browse=True,
            )

    def test_order_line_procurement_data_fdb_ndc_binder(self):
        """ It should get binder for model """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = [mock.MagicMock(),
                                                mock.MagicMock(),
                                                EndTestException]
            with self.assertRaises(EndTestException):
                self.unit.order_line_procurement_data(self.record)
            self.unit.binder_for.assert_called_with(
                'carepoint.fdb.ndc'
            )

    def test_order_line_procurement_fdb_ndc_order_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = [mock.MagicMock(),
                                                          mock.MagicMock(),
                                                          EndTestException]
            with self.assertRaises(EndTestException):
                self.unit.order_line_procurement_data(self.record)
            self.unit.binder_for().to_odoo.assert_called_with(
                self.record['disp_ndc'].strip(), browse=True,
            )

    def test_order_line_procurement_filters_lines(self):
        """ It should filter out non-rx orders """
        with mock.patch.object(self.unit, 'binder_for'):
            filtered = \
                self.unit.binder_for().to_odoo().order_line.filtered
            filtered.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.order_line_procurement_data(self.record)

    def test_order_line_procurement_writes_dispense_data(self):
        """ It write the dispensed data out to the sale line """
        with mock.patch.object(self.unit, 'binder_for'):
            filtered = \
                self.unit.binder_for().to_odoo().order_line.filtered
            write = filtered()[0].write
            write.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.order_line_procurement_data(self.record)
            write.assert_called_once_with({
                'product_id':
                    self.unit.binder_for().to_odoo().
                    medicament_id.product_id.id,
                'product_uom_qty': self.record['dispense_qty'],
            })

    def test_order_line_procurement_searches_proc_group(self):
        """ It should try to find procurement group for sale """
        with mock.patch.object(self.unit, 'binder_for'):
            with mock.patch.object(self.unit.session, 'env') as env:
                search = env['procurement.group'].search
                search.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    self.unit.order_line_procurement_data(self.record)
                search.assert_called_once_with(
                    [('name', '=', self.unit.binder_for().to_odoo().name)],
                    limit=1,
                )

    def test_order_line_procurement_creates_proc_group(self):
        """ It should create new proc group for sale if non-existant """
        with mock.patch.object(self.unit, 'binder_for'):
            with mock.patch.object(self.unit.session, 'env') as env:
                search = env['procurement.group'].search
                create = env['procurement.group'].create
                search.return_value = []
                create.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    self.unit.order_line_procurement_data(self.record)
                create.assert_called_once_with(
                    self.unit.binder_for().to_odoo().
                    _prepare_procurement_group(),
                )

    def test_order_line_procurement_preps_order_line_proc(self):
        """ It should prepare order line procurements """
        with mock.patch.object(self.unit, 'binder_for'):
            with mock.patch.object(self.unit.session, 'env') as env:
                create = env['procurement.group'].create
                line = \
                    self.unit.binder_for().to_odoo().order_line.filtered()[0]
                line._prepare_order_line_procurement.side_effect = \
                    EndTestException
                with self.assertRaises(EndTestException):
                    self.unit.order_line_procurement_data(self.record)
                line._prepare_order_line_procurement.assert_called_once_with(
                    create().id
                )

    def test_order_line_procurement_updates_order_line_proc_vals(self):
        """ It should update procurements w/ CP data """
        with mock.patch.object(self.unit, 'binder_for'):
            with mock.patch.object(self.unit.session, 'env'):
                line = \
                    self.unit.binder_for().to_odoo().order_line.filtered()[0]
                proc = line._prepare_order_line_procurement()
                proc.update.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    self.unit.order_line_procurement_data(self.record)
                proc.update.assert_called_once_with({
                    'origin': self.unit.binder_for().to_odoo().name,
                    'product_uom': line.product_uom.id,
                    'ndc_id': self.unit.binder_for().to_odoo().id,
                    'product_id': line.product_id,
                })

    def test_order_line_procurement_updates_order_line_proc_vals(self):
        """ It should return order procurements dict """
        with mock.patch.object(self.unit, 'binder_for'):
            with mock.patch.object(self.unit.session, 'env'):
                line = \
                    self.unit.binder_for().to_odoo().order_line.filtered()[0]
                proc = line._prepare_order_line_procurement()
                res = self.unit.order_line_procurement_data(self.record)
                self.assertEqual(proc, res)


class TestProcurementOrderImporter(ProcurementOrderTestBase):

    def setUp(self):
        super(TestProcurementOrderImporter, self).setUp()
        self.Unit = procurement_order.ProcurementOrderImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['rx_id'],
                    'carepoint.medical.prescription.order.line',
                ),
                mock.call(
                    self.record['disp_ndc'].strip(),
                    'carepoint.fdb.ndc',
                ),
                mock.call(
                    self.record['order_id'],
                    'carepoint.sale.order'
                ),
            ])
