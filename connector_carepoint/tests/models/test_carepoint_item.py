# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint.models import carepoint_item

from ..common import SetUpCarepointBase


class EndTestException(Exception):
    pass


class CarepointItemTestBase(SetUpCarepointBase):

    def setUp(self):
        super(CarepointItemTestBase, self).setUp()
        self.model = 'carepoint.carepoint.item'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )
        self.record = {
            'ACTIVE_YN': 1,
            'store_id': 2,
            'item_id': 3,
            'NDC': ' ndc ',
            'VENDOR': ' 0001 ',
        }


class TestCarepointItemImportMapper(CarepointItemTestBase):

    def setUp(self):
        super(TestCarepointItemImportMapper, self).setUp()
        self.Unit = carepoint_item.CarepointItemImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_store_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.store_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.carepoint.store'
            )

    def test_store_id_to_odoo(self):
        """ It should get Odoo record for store """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.store_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['store_id'],
            )

    def test_store_id_return(self):
        """ It should return formatted store_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.store_id(self.record)
            expect = self.unit.binder_for().to_odoo()
            self.assertDictEqual({'store_id': expect}, res)

    def test_warehouse_id_get_binder(self):
        """ It should get binder for prescription line """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.warehouse_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.stock.warehouse'
            )

    def test_warehouse_id_to_odoo(self):
        """ It should get Odoo record for store """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.warehouse_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['store_id'],
            )

    def test_warehouse_id_return(self):
        """ It should return formatted warehouse_id """
        with mock.patch.object(self.unit, 'binder_for'):
            res = self.unit.warehouse_id(self.record)
            expect = self.unit.binder_for().to_odoo()
            self.assertDictEqual({'warehouse_id': expect}, res)

    def test_active_yes(self):
        """ It should return correct vals """
        res = self.unit.active(self.record)
        self.assertDictEqual({'active': True}, res)

    def test_active_no(self):
        """ It should return correct vals """
        res = self.unit.active({'ACTIVE_YN': 0})
        self.assertDictEqual({'active': False}, res)

    def test_odoo_id_search(self):
        """ It should search for NDC """
        with mock.patch.object(self.unit.session, 'env') as env:
            self.unit.odoo_id(self.record)
            env[''].search.assert_called_once_with(
                [('name', '=', self.record['NDC'].strip())],
                limit=1,
            )

    def test_odoo_id_return(self):
        """ It should search for NDC """
        with mock.patch.object(self.unit.session, 'env') as env:
            expect = [mock.MagicMock()]
            env[''].search.return_value = expect
            res = self.unit.odoo_id(self.record)
            self.assertDictEqual(
                {'odoo_id': expect[0].medicament_id.id},
                res,
            )

    def test_carepoint_id(self):
        """ It should return correct attribute """
        res = self.unit.carepoint_id(self.record)
        expect = {'carepoint_id': self.record['item_id']}
        self.assertDictEqual(expect, res)


class TestCarepointItemImporter(CarepointItemTestBase):

    def setUp(self):
        super(TestCarepointItemImporter, self).setUp()
        self.Unit = carepoint_item.CarepointItemImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['NDC'].strip(),
                    'carepoint.fdb.ndc.cs.ext',
                ),
                mock.call(
                    self.record['NDC'].strip(),
                    'carepoint.fdb.ndc',
                ),
                mock.call(
                    self.record['VENDOR'].strip(),
                    'carepoint.carepoint.vendor'
                ),
            ])


class TestCarepointItemExportMapper(CarepointItemTestBase):

    def setUp(self):
        super(TestCarepointItemExportMapper, self).setUp()
        self.Unit = carepoint_item.CarepointItemExportMapper
        self.unit = self.Unit(self.mock_env)
        self.record = mock.MagicMock()

    def test_active_yn(self):
        """ It should return correct vals """
        res = self.unit.active_yn(self.record)
        self.assertDictEqual({'ACTIVE_YN': self.record.active}, res)

    def test_export_quantities_on_trigger(self):
        """ It should return correct vals on trigger """
        self.record.trigger_export = True
        res = self.unit.export_quantities(self.record)
        expect = {
            'ONHAND': self.record.store_on_hand,
            'ONORDER': self.record.store_on_order,
        }
        self.assertDictEqual(expect, res)

    def test_export_quantities_unset_trigger(self):
        """ It should unsert trigger_export """
        self.record.trigger_export = True
        self.unit.export_quantities(self.record)
        self.assertFalse(self.record.trigger_export)

    def test_export_quantities_no_trigger(self):
        """ It should not return anytying when no trigger_export """
        self.record.trigger_export = False
        res = self.unit.export_quantities(self.record)
        self.assertEqual(None, res)
