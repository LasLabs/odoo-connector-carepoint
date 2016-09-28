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


class CarepointCarepointPatientDisease(models.Model):
    """ Binding Model for the Carepoint Store """
    _name = 'carepoint.carepoint.patient.disease'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.patient.disease': 'odoo_id'}
    _description = 'Carepoint Patient Disease'
    _cp_lib = 'patient_disease'

    odoo_id = fields.Many2one(
        comodel_name='carepoint.patient.disease',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class CarepointPatientDisease(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.patient.disease'
    _description = 'Carepoint Patient Disease'
    _inherits = {'medical.patient.disease': 'disease_id'}

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.patient.disease',
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
class CarepointPatientDiseaseAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Store """
    _model_name = 'carepoint.carepoint.patient.disease'


@carepoint
class CarepointPatientDiseaseBatchImporter(DelayedBatchImporter):
    _model_name = ['carepoint.carepoint.patient.disease']


@carepoint
class CarepointPatientDiseaseUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.patient.disease'

    def _import_by_patient(self, carepoint_patient_id):
        adapter = self.unit_for(CarepointPatientDiseaseAdapter)
        importer = self.unit_for(CarepointPatientDiseaseImporter)
        for record in adapter.search(pat_id=carepoint_patient_id):
            importer.run(record)


@carepoint
class CarepointPatientDiseaseImportMapper(PartnerImportMapper):
    _model_name = 'carepoint.carepoint.patient.disease'

    direct = [
        ('onset_date', 'diagnosed_date'),
        ('resolution_date', 'healed_date'),
    ]

    @mapping
    def pathology_id(self, record):
        pathology_id = self.env['medical.pathology'].search([
            ('code', '=', record['icd9'].strip()),
            ('code_type_id.name', '=ilike', 'ICD9%'),
        ],
            limit=1,
        )
        return {'pathology_id': pathology_id.id}

    @mapping
    @only_create
    def patient_id(self, record):
        binder = self.binder_for('carepoint.carepoint.patient')
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
class CarepointPatientDiseaseImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.patient.disease']
    _base_mapper = CarepointPatientDiseaseImportMapper

    def _import_dependencies(self):
        record = self.carepoint_record
        self._import_dependency(record['pat_id'],
                                'carepoint.carepoint.patient')
        self._import_dependency(record['caring_md_id'],
                                'carepoint.medical.physician')
        pathology = self.unit_for(MedicalPathologyUnit,
                                  'carepoint.medical.pathology')
        pathology._import_by_code(record['icd9'].strip())

    def _create(self, data):   # pragma: no cover
        binding = super(CarepointPatientDiseaseImporter, self)._create(data)
        add_checkpoint(
            self.session, binding._name, binding.id, binding.backend_id.id
        )
        return binding


@carepoint
class CarepointPatientDiseaseExportMapper(ExportMapper):
    _model_name = 'carepoint.carepoint.patient.disease'

    direct = [
        (none('diagnosed_date'), 'onset_date'),
        (none('healed_date'), 'resolution_date'),
        (m2o_to_backend('patient_id'), 'pat_id'),
        (m2o_to_backend('physician_id'), 'caring_md_id'),
        (follow_m2o_relations('pathology_id.code'), 'icd9'),
    ]


@carepoint
class CarepointPatientDiseaseExporter(CarepointExporter):
    _model_name = 'carepoint.carepoint.patient.disease'
    _base_mapper = CarepointPatientDiseaseExportMapper

    def _export_dependencies(self):
        record = self.carepoint_record
        self._export_dependency(record['pat_id'],
                                'carepoint.carepoint.patient')
        self._export_dependency(record['caring_md_id'],
                                'carepoint.medical.physician')
