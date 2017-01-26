# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from odoo.addons.connector_carepoint.unit import binder

from .common import SetUpCarepointBase


model = 'odoo.addons.connector_carepoint.unit.binder'


class TestBinder(SetUpCarepointBase):

    def setUp(self):
        super(TestBinder, self).setUp()
        self.model = 'carepoint.carepoint.store'
        self.carepoint_id = 1234567
        self.Binder = binder.CarepointModelBinder

    def _new_binder(self):
        return self.Binder(self.get_carepoint_helper(
            self.model
        ))

    def _new_record(self, bind=True):
        return self.env[self.model].create({
            'name': 'Test Pharm',
            'carepoint_id': self.carepoint_id if bind else None,
            'backend_id': self.backend.id,
            'warehouse_id': self.env.ref('stock.warehouse0').id,
        })

    def test_to_odoo_unwrap(self):
        """ It should return internal Id of Odoo record """
        rec = self._new_record()
        binder = self._new_binder()
        res = binder.to_odoo(
            self.carepoint_id,
            unwrap=True,
            browse=False,
        )
        self.assertEqual(rec.odoo_id.id, res)

    def test_to_odoo_unwrap_browse(self):
        """ It should return Odoo record """
        rec = self._new_record()
        binder = self._new_binder()
        res = binder.to_odoo(
            self.carepoint_id,
            unwrap=True,
            browse=True,
        )
        self.assertEqual(rec.odoo_id, res)

    def test_to_odoo_wrap(self):
        """ It should return internal Id of Odoo bind record """
        rec = self._new_record()
        binder = self._new_binder()
        res = binder.to_odoo(
            self.carepoint_id,
            unwrap=False,
            browse=False,
        )
        self.assertEqual(rec.id, res)

    def test_to_odoo_wrap_browse(self):
        """ It should return Odoo bind record """
        rec = self._new_record()
        binder = self._new_binder()
        res = binder.to_odoo(
            self.carepoint_id,
            unwrap=False,
            browse=True,
        )
        self.assertEqual(rec, res)

    def test_to_backend_wrap(self):
        """ It should return return Odoo bind record """
        rec = self._new_record()
        binder = self._new_binder()
        res = binder.to_backend(
            rec.id,
            wrap=True,
        )
        self.assertEqual(rec, res)

    def test_to_backend_wrap(self):
        """ It should properly handle input recordset """
        rec = self._new_record()
        binder = self._new_binder()
        res = binder.to_backend(
            rec,
            wrap=True,
        )
        self.assertEqual(rec.carepoint_id, res)

    def test_to_backend_unwrap(self):
        """ It should return return Odoo bind record id """
        rec = self._new_record()
        binder = self._new_binder()
        res = binder.to_backend(
            rec.id,
            wrap=False,
        )
        self.assertEqual(rec.id, res)

    def test_bind_no_binding(self):
        """ It should not allow False binding """
        binder = self._new_binder()
        with self.assertRaises(AssertionError):
            binder.bind(True, False)

    def test_bind_no_external(self):
        """ It should not allow False external Id """
        binder = self._new_binder()
        with self.assertRaises(AssertionError):
            binder.bind(False, True)

    @mock.patch('%s.odoo' % model)
    def test_bind_context_no_export(self, odoo):
        """ It should use a connector_no_export context """
        binder = self._new_binder()
        rec = mock.MagicMock()
        odoo.models.BaseModel = type(rec)
        binder.bind(self.carepoint_id, rec)
        rec.with_context.assert_called_once_with(
            connector_no_export=True,
        )

    @mock.patch('%s.odoo' % model)
    def test_bind_writes(self, odoo):
        """ It should write binding and sync time to record """
        rec = mock.MagicMock()
        odoo.models.BaseModel = type(rec)
        binder = self._new_binder()
        binder.bind(self.carepoint_id, rec)
        rec.with_context().write.assert_called_once_with({
            'carepoint_id': str(self.carepoint_id),
            'sync_date': odoo.fields.Datetime.now(),
        })

    def test_unwrap_binding_id_browse(self):
        """ It should return normal record given binding id """
        rec = self._new_record()
        binder = self._new_binder()
        self.assertEqual(
            rec.odoo_id,
            binder.unwrap_binding(
                rec.id, browse=True,
            )
        )

    def test_unwrap_binding_record_browse(self):
        """ It should return normal record given binding record """
        rec = self._new_record()
        binder = self._new_binder()
        self.assertEqual(
            rec.odoo_id,
            binder.unwrap_binding(
                rec, browse=True,
            )
        )

    def test_unwrap_binding_id(self):
        """ It should return normal record id given binding id """
        rec = self._new_record()
        binder = self._new_binder()
        self.assertEqual(
            rec.odoo_id.id,
            binder.unwrap_binding(
                rec.id, browse=False,
            )
        )

    def test_unwrap_binding_record(self):
        """ It should return normal record id given binding record """
        rec = self._new_record()
        binder = self._new_binder()
        self.assertEqual(
            rec.odoo_id.id,
            binder.unwrap_binding(
                rec, browse=False,
            )
        )

    def test_unwrap_model_valid(self):
        """ It should return normal model name """
        binder = self._new_binder()
        self.AssertEqual(
            self.model.replace('carepoint.', ''),
            binder.unwrap_model()
        )

    def test_unwrap_model_valid(self):
        """ It should raise ValueError on unbound models """
        self.model = 'res.partner'
        binder = self._new_binder()
        with self.assertRaises(ValueError):
            binder.unwrap_model()
