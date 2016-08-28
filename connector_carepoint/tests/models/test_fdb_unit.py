# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock
from contextlib import contextmanager

from openerp.addons.connector_carepoint.models import fdb_unit

from ..common import SetUpCarepointBase


model = 'openerp.addons.connector_carepoint.models.fdb_unit'


class EndTestException(Exception):
    pass


class FdbUnitTestBase(SetUpCarepointBase):

    def setUp(self):
        super(FdbUnitTestBase, self).setUp()
        self.model = 'carepoint.fdb.unit'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'str': ' e3r3454re ',
            'str60': ' e3r3454re eefefr ',
        }


class TestFdbUnitImportMapper(FdbUnitTestBase):

    def setUp(self):
        super(TestFdbUnitImportMapper, self).setUp()
        self.Unit = fdb_unit.FdbUnitImportMapper
        self.unit = self.Unit(self.mock_env)

    @contextmanager
    def mock_pint(self):
        with mock.patch('%s.ureg' % model) as ureg:
            with mock.patch('%s.infer_base_unit' % model) as infer:
                yield {
                    'ureg': ureg,
                    'infer_base': infer,
                }

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['str'].strip()}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_uom_category_id_search(self):
        """ It should search for UOM categories """
        expect = 'expect'
        with mock.patch.object(self.unit.session, 'env') as env:
            mk = env['product.uom.categ']
            mk.search.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._uom_category_id(expect)
            mk.search.assert_called_once_with(
                [('name', '=', expect)], limit=1,
            )

    def test_uom_category_id_search_return(self):
        """ It should return UOM category from search """
        with mock.patch.object(self.unit.session, 'env') as env:
            mk = env['product.uom.categ']
            mk.search.return_value = [True]
            res = self.unit._uom_category_id(None)
            self.assertEqual(mk.search(), res)

    def test_uom_category_id_create(self):
        """ It should create new UOM categ if not existing """
        expect = 'expect'
        with mock.patch.object(self.unit.session, 'env') as env:
            mk = env['product.uom.categ']
            mk.search.return_value = []
            mk.create.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._uom_category_id(expect)
            mk.create.assert_called_once_with({
                'name': expect,
            })

    def test_uom_category_id_create_return(self):
        """ It should return UOM category from create """
        with mock.patch.object(self.unit.session, 'env') as env:
            mk = env['product.uom.categ']
            mk.search.return_value = []
            res = self.unit._uom_category_id(None)
            self.assertEqual(mk.create(), res)

    def test_uom_id_ureg(self):
        """ It should parse the str60 w/ pint """
        with self.mock_pint() as mk:
            mk['ureg'].side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.uom_id(self.record)
            mk['ureg'].assert_called_once_with(
                self.record['str60'].strip()
            )

    def test_uom_id_ureg_cc(self):
        """ It should have identified and split the CC for ureg parse """
        record = self.record
        record['str60'] = '1cc'
        with self.mock_pint() as mk:
            mk['ureg'].side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.uom_id(record)
            mk['ureg'].assert_called_once_with(
                '1 cc'
            )

    def test_uom_id_ureg_days(self):
        """ It should have identified and split the days for ureg parse """
        record = self.record
        record['str60'] = 'daysx3'
        with self.mock_pint() as mk:
            mk['ureg'].side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.uom_id(record)
            mk['ureg'].assert_called_once_with(
                'days ** 3'
            )

    def test_uom_id_infer_base_unit(self):
        """ It should attempt to infer base of unit """
        with self.mock_pint() as mk:
            mk['infer_base'].side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.uom_id(self.record)
            mk['infer_base'].assert_called_once_with(
                mk['ureg']()
            )

    def test_uom_id_convert_units_to_base(self):
        """ It should attempt to convert units into base """
        with self.mock_pint() as mk:
            mk['ureg']().to.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.uom_id(self.record)
            mk['ureg']().to.assert_called_once_with(
                mk['infer_base']()
            )

    def test_uom_id_gets_category(self):
        """ It should get category for UOM """
        with self.mock_pint() as mk:
            with mock.patch.object(self.unit, '_uom_category_id') as categ:
                categ.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    self.unit.uom_id(self.record)
                categ.assert_called_once_with(
                    str(mk['infer_base']())
                )

    def test_uom_id_search(self):
        """ It should find the base unit record """
        with self.mock_pint() as mk:
            with mock.patch.object(self.unit.session, 'env') as env:
                env['product.uom'].search.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    self.unit.uom_id(self.record)
                env['product.uom'].search.assert_called_once_with(
                    [('name', '=', str(mk['infer_base']()))], limit=1,
                )

    def test_uom_id_returns_existing(self):
        """ It should return existing UOM if found """
        expect = mock.MagicMock()
        with self.mock_pint():
            with mock.patch.object(self.unit.session, 'env') as env:
                env['product.uom'].search.return_value = [expect]
                res = self.unit.uom_id(self.record)
                self.assertDictEqual(
                    {'uom_id': expect.id}, res
                )

    def test_uom_id_root(self):
        """ It should return correct UOM vals if a root unit """
        expect = mock.MagicMock()
        with self.mock_pint() as mk:
            with mock.patch.object(self.unit, '_uom_category_id') as categ:
                with mock.patch.object(self.unit.session, 'env'):
                    mk['ureg'].return_value = expect
                    mk['infer_base'].return_value = expect
                    res = self.unit.uom_id(self.record)
                    expect = {
                        'name': self.record['str'].strip(),
                        'category_id': categ().id,
                        'uom_type': 'reference',
                    }
                    self.assertDictEqual(expect, res)

    def test_uom_id_smaller(self):
        """ It should return correct UOM vals if a smaller unit """
        with self.mock_pint() as mk:
            with mock.patch.object(self.unit, '_uom_category_id') as categ:
                with mock.patch.object(self.unit.session, 'env'):
                    mk['ureg']().to().m = -100
                    mk['infer_base']().m = 100
                    res = self.unit.uom_id(self.record)
                    expect = {
                        'name': self.record['str'].strip(),
                        'category_id': categ().id,
                        'uom_type': 'smaller',
                        'factor': mk['ureg']().m.__rmul__(),
                    }
                    self.assertDictEqual(expect, res)

    def test_uom_id_bigger(self):
        """ It should return correct UOM vals if a bigger unit """
        with self.mock_pint() as mk:
            with mock.patch.object(self.unit, '_uom_category_id') as categ:
                with mock.patch.object(self.unit.session, 'env'):
                    mk['ureg']().to().m = 100
                    mk['infer_base']().m = -100
                    res = self.unit.uom_id(self.record)
                    expect = {
                        'name': self.record['str'].strip(),
                        'category_id': categ().id,
                        'uom_type': 'bigger',
                        'factor': mk['ureg']().m.__rmul__(),
                    }
                    self.assertDictEqual(expect, res)
