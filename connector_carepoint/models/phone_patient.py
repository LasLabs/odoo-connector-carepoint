# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields, api
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..backend import carepoint
from ..unit.import_synchronizer import DelayedBatchImporter

from .phone_abstract import (CarepointPhoneAbstractImportMapper,
                             CarepointPhoneAbstractImporter,
                             CarepointPhoneAbstractExportMapper,
                             CarepointPhoneAbstractExporter,
                             )

_logger = logging.getLogger(__name__)


class CarepointCarepointPhonePatient(models.Model):
    """ Binding Model for the Carepoint Phone Patient """
    _name = 'carepoint.carepoint.phone.patient'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.phone.patient': 'odoo_id'}
    _description = 'Carepoint Phone Patient Many2Many Rel'
    _cp_lib = 'patient_phone'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='carepoint.phone.patient',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class CarepointPhonePatient(models.Model):
    """ Adds the ``One2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.phone.patient'
    _inherit = 'carepoint.phone.abstract'
    _description = 'Carepoint Phone Patient'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.phone.patient',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )

    @api.model
    def _default_res_model(self):
        """ It returns the res model. """
        return 'medical.patient'


@carepoint
class CarepointPhonePatientAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Phone Patient """
    _model_name = 'carepoint.carepoint.phone.patient'


@carepoint
class CarepointPhonePatientBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Phone Patients.
    For every phone in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.phone.patient']


@carepoint
class CarepointPhonePatientImportMapper(
    CarepointPhoneAbstractImportMapper,
):
    _model_name = 'carepoint.carepoint.phone.patient'

    @mapping
    @only_create
    def partner_id(self, record):
        """ It returns either the commercial partner or parent & defaults """
        binder = self.binder_for('carepoint.medical.patient')
        patient_id = binder.to_odoo(record['pat_id'], browse=True)
        _sup = super(CarepointPhonePatientImportMapper, self)
        return _sup.partner_id(
            record, patient_id,
        )

    @mapping
    @only_create
    def res_model_and_id(self, record):
        binder = self.binder_for('carepoint.medical.patient')
        patient_id = binder.to_odoo(record['pat_id'], browse=True)
        _sup = super(CarepointPhonePatientImportMapper, self)
        return _sup.res_model_and_id(
            record, patient_id,
        )

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%d,%d' % (record['pat_id'],
                                           record['phone_id'])}


@carepoint
class CarepointPhonePatientImporter(
    CarepointPhoneAbstractImporter,
):
    _model_name = ['carepoint.carepoint.phone.patient']
    _base_mapper = CarepointPhonePatientImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        super(CarepointPhonePatientImporter, self)._import_dependencies()
        self._import_dependency(self.carepoint_record['pat_id'],
                                'carepoint.medical.patient')


@carepoint
class CarepointPhonePatientUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.phone.patient'

    def _import_phones(self, patient_id, partner_binding):
        adapter = self.unit_for(CarepointCRUDAdapter)
        importer = self.unit_for(CarepointPhonePatientImporter)
        phone_ids = adapter.search(pat_id=patient_id)
        for phone_id in phone_ids:
            importer.run(phone_id)


@carepoint
class CarepointPhonePatientExportMapper(
    CarepointPhoneAbstractExportMapper
):
    _model_name = 'carepoint.carepoint.phone.patient'

    @mapping
    def pat_id(self, binding):
        binder = self.binder_for('carepoint.medical.patient')
        rec_id = binder.to_backend(binding.res_id)
        return {'pat_id': rec_id}


@carepoint
class CarepointPhonePatientExporter(
    CarepointPhoneAbstractExporter
):
    _model_name = 'carepoint.carepoint.phone.patient'
    _base_mapper = CarepointPhonePatientExportMapper
