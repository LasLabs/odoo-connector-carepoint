# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  none,
                                                  m2o_to_backend,
                                                  follow_m2o_relations,
                                                  ExportMapper,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..backend import carepoint
from ..unit.mapper import PartnerImportMapper
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import CarepointExporter

from .medical_pathology import MedicalPathologyUnit


from ..connector import add_checkpoint


_logger = logging.getLogger(__name__)


class CarepointMedicalPatientDisease(models.Model):
    """ Binding Model for the Carepoint Store """
    _name = 'carepoint.medical.patient.disease'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.patient.disease': 'odoo_id'}
    _description = 'Carepoint Patient Disease'
    _cp_lib = 'patient_disease'

    odoo_id = fields.Many2one(
        comodel_name='medical.patient.disease',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class MedicalPatientDisease(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'medical.patient.disease'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.patient.disease',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class MedicalPatientDiseaseAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Store """
    _model_name = 'carepoint.medical.patient.disease'


@carepoint
class MedicalPatientDiseaseBatchImporter(DelayedBatchImporter):
    _model_name = ['carepoint.medical.patient.disease']


@carepoint
class MedicalPatientDiseaseUnit(ConnectorUnit):
    _model_name = 'carepoint.medical.patient.disease'

    def _import_by_patient(self, carepoint_patient_id):
        adapter = self.unit_for(MedicalPatientDiseaseAdapter)
        importer = self.unit_for(MedicalPatientDiseaseImporter)
        for record in adapter.search(pat_id=carepoint_patient_id):
            importer.run(record)


@carepoint
class MedicalPatientDiseaseImportMapper(PartnerImportMapper):
    _model_name = 'carepoint.medical.patient.disease'

    direct = [
        ('onset_date', 'diagnosed_date'),
        ('resolution_date', 'healed_date'),
    ]

    @mapping
    def pathology_id(self, record):
        if not record['icd9']:
            return
        pathology_id = self.env['medical.pathology'].search([
            ('code', '=', record['icd9'].strip()),
            ('code_type_id.name', '=ilike', 'ICD-9%'),
        ],
            limit=1,
        )
        return {'pathology_id': pathology_id.id}

    @mapping
    @only_create
    def patient_id(self, record):
        binder = self.binder_for('carepoint.medical.patient')
        record_id = binder.to_odoo(record['pat_id'])
        return {'patient_id': record_id}

    @mapping
    @only_create
    def physician_id(self, record):
        binder = self.binder_for('carepoint.medical.physician')
        record_id = binder.to_odoo(record['caring_md_id'])
        return {'physician_id': record_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['ptdx_id']}


@carepoint
class MedicalPatientDiseaseImporter(CarepointImporter):
    _model_name = ['carepoint.medical.patient.disease']
    _base_mapper = MedicalPatientDiseaseImportMapper

    def _import_dependencies(self):
        record = self.carepoint_record
        self._import_dependency(record['pat_id'],
                                'carepoint.medical.patient')
        self._import_dependency(record['caring_md_id'],
                                'carepoint.medical.physician')
        if record['icd9']:
            pathology = self.unit_for(MedicalPathologyUnit,
                                      'carepoint.medical.pathology')
            pathology._import_by_code(record['icd9'].strip())

    def _create(self, data):   # pragma: no cover
        binding = super(MedicalPatientDiseaseImporter, self)._create(data)
        add_checkpoint(
            self.session, binding._name, binding.id, binding.backend_id.id
        )
        return binding


@carepoint
class MedicalPatientDiseaseExportMapper(ExportMapper):
    _model_name = 'carepoint.medical.patient.disease'

    direct = [
        (none('diagnosed_date'), 'onset_date'),
        (none('healed_date'), 'resolution_date'),
        (m2o_to_backend('patient_id'), 'pat_id'),
        (m2o_to_backend('physician_id'), 'caring_md_id'),
        (follow_m2o_relations('pathology_id.code'), 'icd9'),
    ]


@carepoint
class MedicalPatientDiseaseExporter(CarepointExporter):
    _model_name = 'carepoint.medical.patient.disease'
    _base_mapper = MedicalPatientDiseaseExportMapper

    def _export_dependencies(self):
        record = self.carepoint_record
        self._export_dependency(record['pat_id'],
                                'carepoint.medical.patient')
        self._export_dependency(record['caring_md_id'],
                                'carepoint.medical.physician')
