# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class CarepointAccount(models.Model):
    _name = 'carepoint.carepoint.account'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.account': 'odoo_id'}
    _description = 'Carepoint Account'
    _cp_lib = 'account'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='Account',
        comodel_name='carepoint.account',
        required=True,
        ondelete='restrict',
    )
    backend_id = fields.Many2one(
        comodel_name='carepoint.backend',
        string='Carepoint Backend',
        store=True,
        readonly=True,
        # override 'carepoint.binding', can't be INSERTed if True:
        required=False,
    )


class Account(models.Model):
    _name = 'carepoint.account'
    _description = 'CarePoint Account'

    patient_id = fields.Many2one(
        string='Patient',
        comodel_name='medical.patient',
    )
    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.account',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class AccountAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.carepoint.account'


@carepoint
class AccountBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Accounts.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.carepoint.account']


@carepoint
class AccountImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.carepoint.account'
    direct = []

    @mapping
    def patient_id(self, record):
        binder = self.binder_for('carepoint.medical.patient')
        patient_id = binder.to_odoo(record['pat_id'])
        return {'patient_id': patient_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['ID']}


@carepoint
class AccountImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.account']

    _base_mapper = AccountImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['pat_id'],
                                'carepoint.medical.patient')
