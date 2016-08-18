# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  changed_by,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (PersonImportMapper,
                           PersonExportMapper,
                           trim,
                           )
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import (CarepointExporter)


_logger = logging.getLogger(__name__)


class CarepointMedicalPatient(models.Model):
    """ Binding Model for the Carepoint Patient """
    _name = 'carepoint.medical.patient'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.patient': 'odoo_id'}
    _description = 'Carepoint Patient'
    _cp_lib = 'patient'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='medical.patient',
        string='Patient',
        required=True,
        ondelete='cascade'
    )
    backend_id = fields.Many2one(
        comodel_name='carepoint.backend',
        string='Carepoint Backend',
        store=True,
        readonly=True,
        # override 'carepoint.binding', can't be INSERTed if True:
        required=False,
    )
    created_at = fields.Date('Created At (on Carepoint)')
    updated_at = fields.Date('Updated At (on Carepoint)')

    _sql_constraints = [
        ('odoo_uniq', 'unique(backend_id, odoo_id)',
         'A Carepoint binding for this patient already exists.'),
    ]


class MedicalPatient(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'medical.patient'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.patient',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class MedicalPatientAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Patient """
    _model_name = 'carepoint.medical.patient'


@carepoint
class MedicalPatientBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Patients.
    For every patient in the list, a delayed job is created.
    """
    _model_name = ['carepoint.medical.patient']


@carepoint
class MedicalPatientImportMapper(PersonImportMapper):
    _model_name = 'carepoint.medical.patient'

    direct = [
        (trim('ssn'), 'ref'),
        (trim('email'), 'email'),
        ('birth_date', 'dob'),
        ('death_date', 'dod'),
    ]

    @mapping
    def gender(self, record):
        gender = record.get('gender_cd')
        if not gender:
            return {'gender': None}
        return {'gender': gender.lower()}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['pat_id']}

    @only_create
    @mapping
    def odoo_id(self, record):
        """ Will bind the patient on a existing patient
        with the same name & dob """
        name = self._get_name(record)
        patient_id = self.env['medical.patient'].search(
            [('name', 'ilike', name), ('dob', '=', record.get('birth_date'))],
            limit=1,
        )
        if patient_id:
            return {'odoo_id': patient_id.id}


@carepoint
class MedicalPatientImporter(CarepointImporter):
    _model_name = ['carepoint.medical.patient']
    _base_mapper = MedicalPatientImportMapper

    #
    # def _after_import(self, partner_binding):
    #     """ Import the addresses """
    #     book = self.unit_for(PartnerAddressBook, model='carepoint.address')
    #     book.import_addresses(self.carepoint_id, partner_binding.id)


@carepoint
class MedicalPatientExportMapper(PersonExportMapper):
    _model_name = 'carepoint.medical.patient'

    direct = [
        ('ref', 'ssn'),
        ('email', 'email'),
        ('dob', 'birth_date'),
        ('dod', 'death_date'),
    ]

    @mapping
    def pat_id(self, record):
        return {'pat_id': record.carepoint_id}

    @mapping
    @changed_by('gender')
    def gender_cd(self, record):
        return {'gender_cd': record.get('gender').upper()}


@carepoint
class MedicalPatientExporter(CarepointExporter):
    _model_name = ['carepoint.medical.patient']
    _base_mapper = MedicalPatientExportMapper
