# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock

from openerp.addons.connector_carepoint import consumer

from .common import SetUpCarepointBase


mk_file = 'openerp.addons.connector_carepoint.consumer'


class TestConsumer(SetUpCarepointBase):

    def setUp(self):
        super(TestConsumer, self).setUp()
        self.model = 'carepoint.carepoint.store'
        self.binding_id = self._new_record()

    def _new_record(self):
        return self.env[self.model].create({
            'name': 'Test Pharm',
            'carepoint_id': 1234567,
            'backend_id': self.backend.id,
            'warehouse_id': self.env.ref('stock.warehouse0').id,
        })

    def test_delay_export_context_no_export(self):
        """ It should not export if context prohibits """
        self.session = mock.MagicMock()
        self.session.context = {'connector_no_export': True}
        res = consumer.delay_export(self.session, 0, 0, 0)
        self.assertEqual(None, res)

    def test_delay_export(self):
        """ It should call export_record.delay w/ proper args """
        fields = {'test': 123, 'test2': 456}
        expect = [self.session, self.model, self.binding_id]
        with mock.patch('%s.export_record' % mk_file) as mk:
            consumer.delay_export(*expect, vals=fields)
            mk.delay.assert_called_once_with(*expect, fields=fields.keys())

    def test_delay_export_all_bindings_context_no_export(self):
        """ It should not export if context prohibits """
        self.session = mock.MagicMock()
        self.session.context = {'connector_no_export': True}
        res = consumer.delay_export_all_bindings(self.session, 0, 0, 0)
        self.assertEqual(None, res)

    def test_delay_export_all_bindings(self):
        """ It should call export_record.delay w/ proper args """
        fields = {'test': 123, 'test2': 456}
        send = [self.session, 'carepoint.store', self.binding_id.odoo_id.id]
        expect = [self.session, self.model, self.binding_id.id]
        with mock.patch('%s.export_record' % mk_file) as mk:
            consumer.delay_export_all_bindings(*send, vals=fields)
            mk.delay.assert_called_once_with(*expect, fields=fields.keys())
