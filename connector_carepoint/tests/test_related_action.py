# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import mock
from contextlib import contextmanager

from openerp import _

from openerp.addons.connector_carepoint import related_action

from .common import SetUpCarepointBase


mk_file = 'openerp.addons.connector_carepoint.related_action'


@contextmanager
def mock_connector_env():
    with mock.patch('%s.ConnectorEnvironment' % mk_file) as env:
        yield env


class StopTestException(Exception):
    pass


class TestRelatedAction(SetUpCarepointBase):

    def setUp(self):
        super(TestRelatedAction, self).setUp()
        self.model = 'carepoint.carepoint.store'
        self.binding_id = self._new_record()
        self.job = mock.MagicMock()
        self.job.args = [self.model, self.binding_id.id]

    def _new_record(self):
        return self.env[self.model].create({
            'name': 'Test Pharm',
            'carepoint_id': 1234567,
            'backend_id': self.backend.id,
            'warehouse_id': self.env.ref('stock.warehouse0').id,
        })

    def test_unwrap_binding_no_binding(self):
        """ It should return None when no binding available """
        self.binding_id.unlink()
        res = related_action.unwrap_binding(self.session, self.job)
        self.assertEqual(None, res)

    def test_unwrap_binding_gets_correct_env(self):
        """ It should init the ConnectorEnv w/ proper args """
        with mock_connector_env() as env:
            env.side_effect = StopTestException
            with self.assertRaises(StopTestException):
                related_action.unwrap_binding(self.session, self.job)
            env.assert_called_once_with(
                self.binding_id.backend_id, self.session, self.model,
            )

    def test_unwrap_binding_gets_connector_unit(self):
        """ It should get the connector_unit w/ proper args """
        expect = 'expect'
        with mock_connector_env() as env:
            env().get_connector_unit.side_effect = StopTestException
            with self.assertRaises(StopTestException):
                related_action.unwrap_binding(
                    self.session, self.job, binder_class=expect
                )
            env().get_connector_unit.assert_called_once_with(expect)

    def test_unwrap_binding_unwraps_model(self):
        """ It should unwrap model from binder """
        with mock_connector_env() as env:
            binder = env().get_connector_unit()
            binder.unwrap_model.side_effect = StopTestException
            with self.assertRaises(StopTestException):
                related_action.unwrap_binding(self.session, self.job)

    def test_unwrap_binding_unwraps_binding(self):
        """ It should call unwrap_binding on binder w/ proper args """
        with mock_connector_env() as env:
            binder = env().get_connector_unit()
            binder.unwrap_binding.side_effect = StopTestException
            with self.assertRaises(StopTestException):
                related_action.unwrap_binding(self.session, self.job)
            binder.unwrap_binding.assert_called_once_with(self.binding_id.id)

    def test_unwrap_binding_guards_value_error(self):
        """ It should use binding record when value error on wrap """
        with mock_connector_env() as env:
            binder = env().get_connector_unit()
            binder.unwrap_model.side_effect = ValueError
            res = related_action.unwrap_binding(self.session, self.job)
            self.assertEqual(self.model, res['res_model'])
            self.assertEqual(self.binding_id.id, res['res_id'])

    def test_unwrap_binding_return(self):
        """ It should return proper action """
        with mock_connector_env() as env:
            binder = env().get_connector_unit()
            res = related_action.unwrap_binding(self.session, self.job)
            expect = {
                'name': _('Related Record'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': binder.unwrap_model(),
                'res_id': binder.unwrap_binding(),
            }
            self.assertDictEqual(expect, res)
