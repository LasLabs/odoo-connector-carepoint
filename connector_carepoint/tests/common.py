# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

"""
Helpers usable in the tests
"""

import importlib
import mock
from contextlib import contextmanager
import openerp.tests.common as common
from openerp.addons.connector.session import ConnectorSession

from carepoint.db import Db as CarepointDb


backend_adapter = 'openerp.addons.connector_carepoint.unit.backend_adapter'


@contextmanager
def mock_job_delay_to_direct(job_path):
    """ Replace the .delay() of a job by a direct call
    job_path is the python path, such as::
      openerp.addons.carepoint.models.stock_picking.export_picking_done
    """
    job_module, job_name = job_path.rsplit('.', 1)
    module = importlib.import_module(job_module)
    job_func = getattr(module, job_name, None)
    assert job_func, "The function %s must exist in %s" % (job_name,
                                                           job_module)

    def clean_args_for_func(*args, **kwargs):
        # remove the special args reserved to .delay()
        kwargs.pop('priority', None)
        kwargs.pop('eta', None)
        kwargs.pop('model_name', None)
        kwargs.pop('max_retries', None)
        kwargs.pop('description', None)
        job_func(*args, **kwargs)

    with mock.patch(job_path) as patched_job:
        # call the direct export instead of 'delay()'
        patched_job.delay.side_effect = clean_args_for_func
        yield patched_job


@contextmanager
def mock_api(instantiated=False):
    """ Mock CarePoint API for testing """
    with mock.patch('%s.Carepoint' % backend_adapter) as API:
        yield API() if instantiated else API


@contextmanager
def mock_adapter(unit):
    """ Mock the backend adapter for testing """
    with mock.patch.object(unit, '_backend_adapter') as API:
        yield API


class CarepointHelper(object):
    """ Emulate a ConnectorEnvironment """

    def __init__(self, env, model_name, backend):
        self.cr = env.cr
        self.model = env[model_name]
        self.backend = backend.get_backend()
        self.backend_record = backend
        self.session = ConnectorSession(
            env.cr,
            env.uid,
            env.context,
        )
        self.connector_unit = {}

    def get_connector_unit(self, unit_class):
        try:
            return self.connector_unit[unit_class]
        except KeyError:
            self.connector_unit[unit_class] = mock.MagicMock()
            return self.connector_unit[unit_class]


class SetUpCarepointBase(common.TransactionCase):
    """ Base class - Test the imports from a Carepoint Mock. """

    def setUp(self):
        super(SetUpCarepointBase, self).setUp()
        self.backend_model = self.env['carepoint.backend']
        self.session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context,
        )
        self.journal = self.env['account.journal'].search(
            [('type', '=', 'general')]
        )[0]
        self.cx_term = self.env.ref('account.account_payment_term_net')
        self.vx_term = self.env.ref('account.account_payment_term_immediate')
        self.cx_tax = self.env['account.tax'].create({
            'name': 'Sales Tax',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 1.23,
        })
        self.vx_tax = self.env['account.tax'].create({
            'name': 'Purchase Tax',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 3.21,
        })
        account_obj = self.env['account.account']
        self.account_payable = account_obj.search([
            ('user_type_id.name', '=', 'Payable')
        ],
            limit=1,
        )
        self.account_receivable = account_obj.search([
            ('user_type_id.name', '=', 'Receivable')
        ],
            limit=1,
        )
        self.account_income = account_obj.search([
            ('user_type_id.name', '=', 'Income')
        ],
            limit=1,
        )
        self.account_expense = account_obj.search([
            ('user_type_id.name', '=', 'Expenses')
        ],
            limit=1,
        )
        self.backend = self.backend_model.create({
            'name': 'Test Carepoint',
            'version': '2.99',
            'server': '127.0.0.1',
            'username': 'test',
            'password': 'pass',
            'db_driver': CarepointDb.SQLITE,
            'default_customer_payment_term_id': self.cx_term.id,
            'default_supplier_payment_term_id': self.vx_term.id,
            'default_payment_journal': self.journal.id,
            'default_purchase_tax': self.vx_tax.id,
            'default_sale_tax': self.cx_tax.id,
            'default_account_payable_id': self.account_payable.id,
            'default_account_receivable_id': self.account_receivable.id,
            'default_product_income_account_id': self.account_income.id,
            'default_product_expense_account_id': self.account_expense.id,
        })
        self.mock_api = mock_api
        self.mock_adapter = mock_adapter

    def get_carepoint_helper(self, model_name):
        return CarepointHelper(
            self.env, model_name, self.backend
        )
