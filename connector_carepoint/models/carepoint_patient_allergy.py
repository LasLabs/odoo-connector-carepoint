# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..backend import carepoint
from ..unit.mapper import PartnerImportMapper, trim
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

from .medical_pathology import MedicalPathologyUnit


from ..connector import add_checkpoint


_logger = logging.getLogger(__name__)


class CarepointCarepointPatientAllergy(models.Model):
    """ Binding Model for the Carepoint Store """
    _name = 'carepoint.carepoint.patient.allergy'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.patient.allergy': 'odoo_id'}
    _description = 'Carepoint Patient Allergy'
    _cp_lib = 'patient_allergy'

    odoo_id = fields.Many2one(
        comodel_name='carepoint.patient.allergy',
        string='Allergy',
        required=True,
        ondelete='cascade'
    )


class CarepointPatientAllergy(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.patient.allergy'
    _description = 'Carepoint Patient Allergy'
    _inherits = {'medical.patient.disease': 'disease_id'}

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.patient.allergy',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )
    disease_id = fields.Many2one(
        string='Disease',
        comodel_name='medical.patient.disease',
        required=True,
        ondelete='cascade',
    )


@carepoint
class CarepointPatientAllergyAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Store """
    _model_name = 'carepoint.carepoint.patient.allergy'


@carepoint
class CarepointPatientAllergyBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Stores.
    For every company in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.patient.allergy']


@carepoint
class CarepointPathologyLineUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.pathology'

    def _import_by_patient(self, carepoint_patient_id):
        adapter = self.unit_for(CarepointPatientAllergyAdapter)
        importer = self.unit_for(CarepointPatientAllergyImporter)
        for record in adapter.search(pat_id=carepoint_patient_id):
            importer.run(record)


@carepoint
class CarepointPatientAllergyImportMapper(PartnerImportMapper):
    _model_name = 'carepoint.carepoint.patient.allergy'

    direct = [
        ('add_date', 'created_at'),
        ('chg_date', 'updated_at'),
    ]

    @mapping
    def pathology_id(self, record):
        pathology = self.env.ref(
            'connector_carepoint.pathology_carepoint_allergy'
        )
        return {'pathology_id': pathology.id}

    @mapping
    @only_create
    def patient_id(self, record):
        binder = self.binder_for('carepoint.carepoint.patient')
        record_id = binder.to_odoo(record['pat_id'])
        return {'patient_id': record_id}

    @mapping
    @only_create
    def physician_id(self, record):
        binder = self.binder_for('carepoint.carepoint.physician')
        record_id = binder.to_odoo(record['caring_md_id'])
        return {'physician_id': record_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['ptdx_id']}


@carepoint
class CarepointPatientAllergyImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.patient.allergy']
    _base_mapper = CarepointPatientAllergyImportMapper

    def _import_dependencies(self):
        record = self.carepoint_record
        self._import_dependency(record['pat_id'],
                                'carepoint.carepoint.patient')
        self._import_dependency(record['caring_md_id'],
                                'carepoint.carepoint.physician')
        pathology = self.unit_for(MedicalPathologyUnit,
                                 'carepoint.carepoint.pathology')
        pathology._import_by_code(record['icd9'].strip())

    def _create(self, data):   # pragma: no cover
        binding = super(CarepointPatientAllergyImporter, self)._create(data)
        add_checkpoint(
            self.session, binding._name, binding.id, binding.backend_id.id
        )
        return binding
