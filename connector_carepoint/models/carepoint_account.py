# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api
from odoo.addons.connector.connector import ConnectorUnit
from odoo.addons.connector.unit.mapper import (mapping,
                                               ExportMapper,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import CarepointExporter

_logger = logging.getLogger(__name__)


class CarepointAccount(models.Model):
    _name = 'carepoint.account'
    _description = 'CarePoint CarepointAccount'

    patient_id = fields.Many2one(
        string='Patient',
        comodel_name='medical.patient',
    )
    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.account',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )

    @api.model
    def _get_by_patient(self, patient, create=True, recurse=False):
        """ It returns the account associated to the patient.
        Params:
            patient: Recordset singleton of partner to search for
            create: Bool determining whether to create account if not exist
            recurse: Bool determining whether to recurse into children (this
                is only functional when create=True)
        Return:
            Recordset of patient account
        """
        account = self.search([('patient_id', '=', patient.id)], limit=1)
        if not create:
            return account
        if not account:
            account = self.create({
                'patient_id': patient.id,
            })
        if recurse:
            children = self.env['medical.patient'].search([
                ('partner_id', 'in', patient.child_ids.ids),
            ])
            for child in children:
                self._get_by_patient(child, create, recurse)
        return account


class CarepointCarepointAccount(models.Model):
    _name = 'carepoint.carepoint.account'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.account': 'odoo_id'}
    _description = 'Carepoint CarepointAccount'
    _cp_lib = 'account'

    odoo_id = fields.Many2one(
        string='CarepointAccount',
        comodel_name='carepoint.account',
        required=True,
        ondelete='restrict',
    )


@carepoint
class CarepointAccountAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.carepoint.account'

    def create(self, data):
        """ Wrapper to create a record on the external system
        Params:
            data: ``dict`` of Data to create record with
        Returns:
            ``str`` of external carepoint_id
        """
        data['ID'] = self.carepoint.get_next_sequence('acct_id')
        return super(CarepointAccountAdapter, self).create(data)


@carepoint
class CarepointAccountUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.account'

    def _import_accounts(self, patient_id):
        adapter = self.unit_for(CarepointAccountAdapter)
        importer = self.unit_for(CarepointAccountImporter)
        accounts = adapter.search(pat_id=patient_id)
        for account in accounts:
            importer.run(account)


@carepoint
class CarepointAccountBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint CarepointAccounts.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.carepoint.account']


@carepoint
class CarepointAccountImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.carepoint.account'
    direct = []

    @mapping
    def patient_id(self, record):
        binder = self.binder_for('carepoint.medical.patient')
        patient_id = binder.to_odoo(record['pat_id'])
        return {'patient_id': patient_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%s,%s' % (record['pat_id'], record['ID'])}


@carepoint
class CarepointAccountImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.account']
    _base_mapper = CarepointAccountImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['pat_id'],
                                'carepoint.medical.patient')


@carepoint
class CarepointAccountExportMapper(ExportMapper):
    _model_name = 'carepoint.carepoint.account'
    direct = []

    @mapping
    def pat_id(self, binding):
        binder = self.binder_for('carepoint.medical.patient')
        patient_id = binder.to_backend(binding.patient_id)
        return {'pat_id': patient_id}

    @mapping
    def ID(self, binding):
        return {'ID': binding.carepoint_id}

    @mapping
    def static_defaults(self, binding):
        return {
            'acct_type_cn': 0,
            'resp_pty_yn': 0,
            'chromis_id': None,
        }


@carepoint
class CarepointAccountExporter(CarepointExporter):
    _model_name = 'carepoint.carepoint.account'
    _base_mapper = CarepointAccountExportMapper

    def _export_dependencies(self):
        """ Export depends for a record """
        self._export_dependency(self.binding_record.patient_id,
                                'carepoint.medical.patient')
