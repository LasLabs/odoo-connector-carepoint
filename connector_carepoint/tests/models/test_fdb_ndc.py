# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock
from contextlib import contextmanager

from openerp.addons.connector_carepoint.models import fdb_ndc

from ..common import SetUpCarepointBase


model = 'openerp.addons.connector_carepoint.models.fdb_ndc'


class EndTestException(Exception):
    pass


class FdbNdcTestBase(SetUpCarepointBase):

    def setUp(self):
        super(FdbNdcTestBase, self).setUp()
        self.model = 'carepoint.fdb.ndc'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'gcn_seqno': 1,
            'ndc': ' 1234567890 ',
            'gpi': 2,
            'dea': 3,
            'hcfa_unit': 4,
            'lblrid': ' lblrid ',
            'bn': '  bn  ',
        }


class TestFdbNdcImportMapper(FdbNdcTestBase):

    def setUp(self):
        super(TestFdbNdcImportMapper, self).setUp()
        self.Unit = fdb_ndc.FdbNdcImportMapper
        self.unit = self.Unit(self.mock_env)

    @contextmanager
    def mock_pint(self):
        with mock.patch('%s.ureg' % model) as ureg:
            yield {
                'ureg': ureg,
            }

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['ndc'].strip()}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_get_uom_parts_percent_replace(self):
        """ It should replace percent signs in favor of word """
        mk = mock.MagicMock()
        mk.replace.side_effect = EndTestException
        with self.assertRaises(EndTestException):
            self.unit._get_uom_parts(mk)
        mk.replace.assert_called_once_with('%', 'percent')

    def test_get_uom_parts_default_unit(self):
        """ It should default to `unit` when no matches """
        expect = ''
        with self.mock_pint() as pint:
            pint['ureg'].side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._get_uom_parts(expect)
            pint['ureg'].assert_called_once_with('unit')

    def test_get_uom_parts_default_regex_unit(self):
        """ It should default to `unit` with a regex match """
        expect = '2'
        with self.mock_pint() as pint:
            pint['ureg'].side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._get_uom_parts(expect)
            pint['ureg'].assert_called_once_with('2 unit')

    def test_get_uom_parts_regex(self):
        """ It should properly extract uom str using regex """
        expect = '12.01 mg'
        with self.mock_pint() as pint:
            pint['ureg'].side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._get_uom_parts(expect)
            pint['ureg'].assert_called_once_with(expect)

    def test_get_uom_parts_regex_multiple(self):
        """ It should properly extract first UOM """
        expect1, expect2 = '12 mg', '9 ml'
        with self.mock_pint() as pint:
            pint['ureg'].side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._get_uom_parts('%s - %s' % (expect1, expect2))
            pint['ureg'].assert_called_once_with(
                expect1
            )

    def test_get_uom_parts_numeric(self):
        """ It should properly handle numeric only data """
        expect = '2'
        with self.mock_pint() as pint:
            pint['ureg']().m = expect
            res = self.unit._get_uom_parts(expect)
            self.assertEqual(
                (float(expect), 'UNIT'), res,
            )

    def test_get_uom_parts_one(self):
        """ It should properly handle one uom in str """
        expect1, expect2 = '2', 'mg'
        with self.mock_pint() as pint:
            pint['ureg']().m = expect1
            res = self.unit._get_uom_parts('%s %s' % (expect1, expect2))
            self.assertEqual(
                (float(expect1), expect2.upper()), res,
            )

    def test_uom_id_search(self):
        """ It should search for UOM id """
        expect = ' expect '
        with mock.patch.object(self.unit.session, 'env') as env:
            mk = env['product.uom']
            mk.search.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._get_uom_id(expect)
            mk.search.assert_called_once_with(
                [('name', '=', expect.strip().upper())], limit=1,
            )

    def test_uom_id_search_return(self):
        """ It should return UOM id from search """
        with mock.patch.object(self.unit.session, 'env') as env:
            mk = env['product.uom']
            res = self.unit._get_uom_id('None')
            self.assertEqual(mk.search(), res)

    def test_get_categ_id_prescription(self):
        """ It should return Rx category for prescription item """
        expect = 'medical_prescription_sale.product_category_rx'
        self.assertEqual(
            self.env.ref(expect),
            self.unit._get_categ_id(True, self.record),
        )

    def test_get_categ_id_otc(self):
        """ It should return Otc category for non-prescription item """
        expect = 'medical_prescription_sale.product_category_otc'
        self.assertEqual(
            self.env.ref(expect),
            self.unit._get_categ_id(False, self.record),
        )

    def test_get_medicament_vals_binders(self):
        """ It should get all binders for medicament vals """
        with mock.patch.object(self.unit, 'binder_for') as mk:
            mk.to_odoo.side_effect = [None, None, EndTestException]
            mk.side_effect = [mk, mk, mk]
            with self.assertRaises(EndTestException):
                self.unit._get_medicament_vals(self.record)
            mk.assert_has_calls([
                mock.call('carepoint.fdb.gcn'),
                mock.call.to_odoo(self.record['gcn_seqno'], browse=True),
                mock.call('carepoint.fdb.ndc.cs.ext'),
                mock.call.to_odoo(self.record['ndc'].strip(), browse=True),
                mock.call('carepoint.fdb.gcn.seq'),
                mock.call.to_odoo(self.record['gcn_seqno'], browse=True),
            ])

    def test_medicament_id_gets_vals(self):
        """ It should get medicament vals for use """
        with mock.patch.object(self.unit, '_get_medicament_vals') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.medicament_id(self.record)
            mk.assert_called_once_with(self.record)

    def test_medicament_id_search(self):
        """ It should search for existing medicaments w/ right vals """
        with mock.patch.object(self.unit, '_get_medicament_vals') as mk:
            with mock.patch.object(self.unit.session, 'env') as env:
                # Return the call arg, allowing for check of key calls
                mk().__getitem__.side_effect = lambda key: key
                env[''].search.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    self.unit.medicament_id(self.record)
                calls = env[''].search.call_args_list
                self.assertLess(
                    0, len(calls),
                )
                for domain in calls[0][0][0]:
                    self.assertEqual('=', domain[1])
                    self.assertEqual(domain[0], domain[2])
                self.assertEqual({'limit': 1}, calls[0][1])

    def test_medicament_id_create(self):
        """ It should create medicament if one doesn't exist """
        with mock.patch.object(self.unit, '_get_medicament_vals') as mk:
            with mock.patch.object(self.unit.session, 'env') as env:
                env[''].search.return_value = []
                env[''].create.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    self.unit.medicament_id(self.record)
                env[''].create.assert_called_once_with(
                    mk(),
                )

    def test_medicament_id_create_error(self):
        """ It should guard IntegrityError and raise ValidationEror """
        with mock.patch.object(self.unit, '_get_medicament_vals'):
            with mock.patch.object(self.unit.session, 'env') as env:
                env[''].search.return_value = []
                env[''].create.side_effect = fdb_ndc.IntegrityError
                with self.assertRaises(fdb_ndc.ValidationError):
                    self.unit.medicament_id(self.record)

    def test_medicament_id_write(self):
        """ It should write to existing medicament if found """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, '_get_medicament_vals') as mk:
            with mock.patch.object(self.unit.session, 'env') as env:
                env[''].search.return_value = [expect]
                expect.write.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    self.unit.medicament_id(self.record)
                expect.write.assert_called_once_with(
                    mk(),
                )

    def test_medicament_id_returns_medicament_id_create(self):
        """ It should return proper value for mapping on create """
        with mock.patch.object(self.unit, '_get_medicament_vals'):
            with mock.patch.object(self.unit.session, 'env') as env:
                env[''].search.return_value = []
                res = self.unit.medicament_id(self.record)
                self.assertEqual(
                    {'medicament_id': env[''].create()[0].id},
                    res,
                )

    def test_medicament_id_returns_medicament_id_write(self):
        """ It should return proper value for mapping on write """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, '_get_medicament_vals'):
            with mock.patch.object(self.unit.session, 'env') as env:
                env[''].search.return_value = [expect]
                res = self.unit.medicament_id(self.record)
                self.assertEqual(
                    {'medicament_id': expect.id},
                    res,
                )

    def test_lbl_mfg_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.lbl_mfg_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.fdb.lbl.rid'
            )

    def test_lbl_mfg_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.lbl_mfg_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['lblrid'].strip(),
            )

    def test_lbl_mfg_id_return(self):
        """ It should return proper vals dict """
        with mock.patch.object(self.unit, 'binder_for'):
            lbl_mfg_id = self.unit.binder_for().to_odoo()
            expect = {'lbl_mfg_id': lbl_mfg_id}
            res = self.unit.lbl_mfg_id(self.record)
            self.assertDictEqual(expect, res)


class TestFdbNdcImporter(FdbNdcTestBase):

    def setUp(self):
        super(TestFdbNdcImporter, self).setUp()
        self.Unit = fdb_ndc.FdbNdcImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all dependencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['ndc'],
                    'carepoint.fdb.ndc.cs.ext',
                ),
                mock.call(
                    self.record['gcn_seqno'],
                    'carepoint.fdb.gcn',
                ),
            ])

    def test_after_import_unit(self):
        """ It should get proper unit """
        with mock.patch.object(self.unit, 'unit_for'):
            self.unit._after_import(None)
            self.unit.unit_for.assert_called_once_with(
                fdb_ndc.FdbImgIdUnit,
                model='carepoint.fdb.img.id',
            )

    def test_after_import_import(self):
        """ It should run import method on unit """
        with mock.patch.object(self.unit, 'unit_for'):
            self.unit._after_import(None)
            self.unit.unit_for()._import_by_ndc.assert_called_once_with(
                self.record['ndc'].strip(),
            )
