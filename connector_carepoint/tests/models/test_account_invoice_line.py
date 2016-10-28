# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.models import account_invoice_line

from ..common import SetUpCarepointBase


model = 'odoo.addons.connector_carepoint.models.account_invoice_line'


class EndTestException(Exception):
    pass


class AccountInvoiceLineTestBase(SetUpCarepointBase):

    def setUp(self):
        super(AccountInvoiceLineTestBase, self).setUp()
        self.model = 'carepoint.account.invoice.line'
        self.mock_env = self.get_carepoint_helper(
            self.model
        )

    @property
    def record(self):
        """ Model record fixture """
        return {
            'rxdisp_id': 12345,
            'primary_pay_date': '2016-01-23 01:23:45',
            't_patient_pay_sub': '10.23',
        }


class TestAccountInvoiceLineUnit(AccountInvoiceLineTestBase):

    def setUp(self):
        super(TestAccountInvoiceLineUnit, self).setUp()
        self.Unit = account_invoice_line.AccountInvoiceLineUnit
        self.unit = self.Unit(self.mock_env)

    def test_import_invoice_lines_for_procurement_unit_for_adapter(self):
        """ It should get unit for adapter """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_invoice_lines_for_procurement(True)
            mk.assert_called_once_with(
                account_invoice_line.CarepointCRUDAdapter
            )

    def test_import_invoice_lines_for_procurement_unit_for_importer(self):
        """ It should get unit for importer """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk.side_effect = [None, EndTestException]
            with self.assertRaises(EndTestException):
                self.unit._import_invoice_lines_for_procurement(True)
            mk.assert_called_with(
                account_invoice_line.AccountInvoiceLineImporter
            )

    def test_import_invoice_lines_for_procurement_search(self):
        """ It should search adapter for unit """
        expect = 'expect'
        with mock.patch.object(self.unit, 'unit_for') as mk:
            mk().search.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_invoice_lines_for_procurement(expect)
            mk().search.assert_called_once_with(
                rxdisp_id=expect,
            )

    def test_import_invoice_lines_for_procurement_imports(self):
        """ It should run importer on records """
        with mock.patch.object(self.unit, 'unit_for') as mk:
            expect = mock.MagicMock()
            adapter = mock.MagicMock()
            adapter.search.return_value = [True]
            mk.side_effect = [adapter, expect]
            expect.run.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._import_invoice_lines_for_procurement(True)
            expect.run.assert_called_once_with(
                adapter.search()[0]
            )


class TestAccountInvoiceLineImportMapper(AccountInvoiceLineTestBase):

    def setUp(self):
        super(TestAccountInvoiceLineImportMapper, self).setUp()
        self.Unit = account_invoice_line.AccountInvoiceLineImportMapper
        self.unit = self.Unit(self.mock_env)

    def test_carepoint_id(self):
        """ It should return correct attribute """
        expect = {'carepoint_id': self.record['rxdisp_id']}
        res = self.unit.carepoint_id(self.record)
        self.assertDictEqual(expect, res)

    def test_invoice_id_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.invoice_id(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.procurement.order'
            )

    def test_invoice_id_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.invoice_id(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['rxdisp_id'], browse=True,
            )

    def test_invoice_id_search(self):
        """ It should search for invoice from origin """
        with mock.patch.object(self.unit, 'binder_for'):
            with mock.patch.object(self.unit.session, 'env') as env:
                env['account.invoice'].search.side_effect = EndTestException
                proc_id = self.unit.binder_for().to_odoo()
                with self.assertRaises(EndTestException):
                    self.unit.invoice_id(self.record)
                env['account.invoice'].search.assert_called_once_with(
                    [('origin', '=', proc_id.sale_line_id.order_id.name)],
                    limit=1,
                )

    def test_invoice_id_existing_invoice(self):
        """ It should return existing matches invoice """
        expect = mock.MagicMock()
        with mock.patch.object(self.unit, 'binder_for'):
            with mock.patch.object(self.unit.session, 'env') as env:
                env['account.invoice'].search.return_value = [expect]
                res = self.unit.invoice_id(self.record)
                expect = {
                    'invoice_id': expect.id,
                }
                self.assertDictEqual(res, expect)

    def test_invoice_id_new_invoice_prepare_invoice(self):
        """ It should prepare invoice from sale order if not existing """
        with mock.patch.object(self.unit, 'binder_for') as mk:
            with mock.patch.object(self.unit.session, 'env') as env:
                env['account.invoice'].search.return_value = []
                prep = mk().to_odoo().sale_line_id.order_id._prepare_invoice
                prep.side_effect = EndTestException
                with self.assertRaises(EndTestException):
                    self.unit.invoice_id(self.record)

    def test_invoice_id_new_invoice_updates_invoice_date(self):
        """ It should inject remote date into invoice vals """
        with mock.patch.object(self.unit, 'binder_for') as mk:
            with mock.patch.object(self.unit.session, 'env') as env:
                env['account.invoice'].search.return_value = []
                prep = mk().to_odoo().sale_line_id.order_id._prepare_invoice
                self.unit.invoice_id(self.record)
                prep().update.assert_called_once_with({
                    'date_invoice': self.record['primary_pay_date'],
                })

    def test_invoice_id_new_invoice_create(self):
        """ It should create invoice with proper vals """
        with mock.patch.object(self.unit, 'binder_for') as mk:
            with mock.patch.object(self.unit.session, 'env') as env:
                env['account.invoice'].search.return_value = []
                prep = mk().to_odoo().sale_line_id.order_id._prepare_invoice
                self.unit.invoice_id(self.record)
                env['account.invoice'].create.assert_called_once_with(prep())

    def test_invoice_id_new_invoice_create_return(self):
        """ It should return result of create in values """
        with mock.patch.object(self.unit, 'binder_for'):
            with mock.patch.object(self.unit.session, 'env') as env:
                env['account.invoice'].search.return_value = []
                res = self.unit.invoice_id(self.record)
                expect = {'invoice_id': env['account.invoice'].create().id}
                self.assertDictEqual(expect, res)

    def test_sale_line_ids_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.sale_line_ids(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.procurement.order'
            )

    def test_sale_line_ids_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.sale_line_ids(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['rxdisp_id'], browse=True,
            )

    def test_sale_line_ids_return(self):
        """ It should return proper values dict """
        with mock.patch.object(self.unit, 'binder_for') as mk:
            res = self.unit.sale_line_ids(self.record)
            expect = {
                'sale_line_ids': [(6, 0, [mk().to_odoo().sale_line_id.id])]
            }
            self.assertDictEqual(expect, res)

    def test_invoice_line_data_get_binder(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.invoice_line_data(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.procurement.order'
            )

    def test_invoice_line_data_to_odoo(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit.invoice_line_data(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['rxdisp_id'], browse=True,
            )

    def test_invoice_line_data_sets_price_unit(self):
        """ It should set the price_unit on sale line to circumvent lack
        of price data in the remote sales records
        """
        qty = 20
        with mock.patch.object(self.unit, 'binder_for'):
            line_id = self.unit.binder_for().to_odoo().sale_line_id
            line_id.product_uom_qty = qty
            self.unit.invoice_line_data(self.record)
            self.assertEqual(
                float(self.record['t_patient_pay_sub']) / qty,
                line_id.price_unit
            )

    def test_invoice_line_data_prepares_invoice_line(self):
        """ It should prepare invoice line based on sale line """
        qty = 20
        with mock.patch.object(self.unit, 'binder_for'):
            line_id = self.unit.binder_for().to_odoo().sale_line_id
            line_id.product_uom_qty = qty
            self.unit.invoice_line_data(self.record)
            line_id._prepare_invoice_line.assert_called_once_with(qty)

    def test_invoice_line_data_return(self):
        """ It should prepare invoice line based on sale line """
        qty = 20
        with mock.patch.object(self.unit, 'binder_for'):
            line_id = self.unit.binder_for().to_odoo().sale_line_id
            line_id.product_uom_qty = qty
            res = self.unit.invoice_line_data(self.record)
            self.assertEqual(line_id._prepare_invoice_line(), res)


class TestAccountInvoiceLineImporter(AccountInvoiceLineTestBase):

    def setUp(self):
        super(TestAccountInvoiceLineImporter, self).setUp()
        self.Unit = account_invoice_line.AccountInvoiceLineImporter
        self.unit = self.Unit(self.mock_env)
        self.unit.carepoint_record = self.record

    def test_import_dependencies(self):
        """ It should import all depedencies """
        with mock.patch.object(self.unit, '_import_dependency') as mk:
            self.unit._import_dependencies()
            mk.assert_has_calls([
                mock.call(
                    self.record['rxdisp_id'],
                    'carepoint.procurement.order',
                ),
            ])

    def test_after_import_get_binder_procurement(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)
            self.unit.binder_for.assert_called_once_with(
                'carepoint.procurement.order'
            )

    def test_after_import_to_odoo_procurement(self):
        """ It should get Odoo record for binding """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)
            self.unit.binder_for().to_odoo.assert_called_once_with(
                self.record['rxdisp_id'], browse=True,
            )

    def test_after_import_get_binder_sale(self):
        """ It should get binder for record type """
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for.side_effect = [mock.MagicMock(),
                                                EndTestException]
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)
            self.unit.binder_for.assert_called_with(
                'carepoint.sale.order'
            )

    def test_after_import_to_backend_sale(self):
        """ It should get backend record for binding """
        proc = mock.MagicMock()
        with mock.patch.object(self.unit, 'binder_for'):
            self.unit.binder_for().to_odoo.return_value = proc
            self.unit.binder_for().to_backend.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)
            self.unit.binder_for().to_backend.assert_called_with(
                proc.sale_line_id.order_id.id,
            )

    def test_after_import_gets_proc_unit(self):
        """ It should get unit for model """
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT
        ):
            self.unit.unit_for.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)
            self.unit.unit_for.assert_called_with(
                account_invoice_line.ProcurementOrderUnit,
                model='carepoint.procurement.order',
            )

    def test_after_import_gets_order_line_cnt(self):
        """ It should get count of order lines for sale """
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT
        ):
            self.unit.unit_for()._get_order_line_count.side_effect = \
                EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)
            self.unit.unit_for()._get_order_line_count.assert_called_with(
                self.unit.binder_for().to_backend()
            )

    def test_after_import_gets_ref_for_cp_state(self):
        """ It should get reference for carepoint state record """
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT,
            session=mock.DEFAULT, _get_binding=mock.DEFAULT,
        ):
            invoice_id = self.unit._get_binding().invoice_id
            self.unit.unit_for()._get_order_line_count.return_value = 1
            invoice_id.invoice_line_ids = [True]
            self.unit.env.ref.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)
            self.unit.env.ref.assert_called_with(
                'connector_carepoint.state_%d' % (
                    self.unit.binder_for().to_odoo().sale_line_id.
                    order_id.carepoint_order_state_cn
                )
            )

    def test_after_import_invoice_write_new_state(self):
        """ It should write to invoice new states provided by remote system """
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT,
            session=mock.DEFAULT, _get_binding=mock.DEFAULT,
        ):
            invoice_id = self.unit._get_binding().invoice_id
            self.unit.unit_for()._get_order_line_count.return_value = 1
            invoice_id.invoice_line_ids = [True]
            invoice_id.write.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)
            invoice_id.write.assert_called_once_with({
                'state': self.unit.env.ref().invoice_state,
            })

    def test_after_import_invoice_create_moves(self):
        """ It should create accounting moves for newly paid invoices """
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT,
            session=mock.DEFAULT, _get_binding=mock.DEFAULT,
        ):
            invoice_id = self.unit._get_binding().invoice_id
            self.unit.unit_for()._get_order_line_count.return_value = 1
            invoice_id.invoice_line_ids = [True]
            self.unit.env.ref().invoice_state = 'paid'
            invoice_id.action_move_create.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)

    def test_after_import_invoice_validate(self):
        """ It should validate newly paid invoices """
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT,
            session=mock.DEFAULT, _get_binding=mock.DEFAULT,
        ):
            invoice_id = self.unit._get_binding().invoice_id
            self.unit.unit_for()._get_order_line_count.return_value = 1
            invoice_id.invoice_line_ids = [True]
            self.unit.env.ref().invoice_state = 'paid'
            invoice_id.invoice_validate.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)

    def test_after_import_invoice_validate(self):
        """ It should pay and reconcile invoices when residual on invoice """
        with mock.patch.multiple(
            self.unit, binder_for=mock.DEFAULT, unit_for=mock.DEFAULT,
            session=mock.DEFAULT, _get_binding=mock.DEFAULT,
        ):
            invoice_id = self.unit._get_binding().invoice_id
            invoice_id.residual = 1
            self.unit.unit_for()._get_order_line_count.return_value = 1
            invoice_id.invoice_line_ids = [True]
            self.unit.env.ref().invoice_state = 'paid'
            invoice_id.pay_and_reconcile.side_effect = EndTestException
            with self.assertRaises(EndTestException):
                self.unit._after_import(self.record)
            invoice_id.pay_and_reconcile.assert_called_once_with(
                self.unit.backend_record.default_payment_journal,
                date=invoice_id.date_invoice,
            )
