# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  changed_by,
                                                  only_create,
                                                  none,
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
from ..unit.export_synchronizer import CarepointExporter

from .address_patient import CarepointAddressPatientUnit
from .carepoint_account import CarepointAccountUnit

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
        (none('birth_date'), 'dob'),
        (none('death_date'), 'dod'),
        ('pat_status_cn', 'active'),
    ]

    @mapping
    def safety_cap_yn(self, record):
        return {'safety_caps_yn': not record['no_safety_caps_yn']}

    @mapping
    def gender(self, record):
        gender = record.get('gender_cd')
        if not gender:
            return {'gender': None}
        return {'gender': gender.lower()}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['pat_id']}

    @mapping
    @only_create
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

    def _after_import(self, partner_binding):
        """ Import the addresses and accounts """
        book = self.unit_for(CarepointAddressPatientUnit,
                             model='carepoint.carepoint.address.patient')
        book._import_addresses(self.carepoint_id, partner_binding)
        account = self.unit_for(CarepointAccountUnit,
                                model='carepoint.carepoint.account')
        account._import_accounts(self.carepoint_id)


@carepoint
class MedicalPatientExportMapper(PersonExportMapper):
    _model_name = 'carepoint.medical.patient'

    direct = [
        (none('ref'), 'ssn'),
        (none('email'), 'email'),
        (none('dob'), 'birth_date'),
        (none('dod'), 'death_date'),
        ('active', 'pat_status_cn')
    ]

    @mapping
    @changed_by('gender')
    def gender_cd(self, record):
        if record.gender:
            return {'gender_cd': record.gender.upper()}

    @mapping
    def static_defaults(self, record):
        """ It provides all static default mappings """
        return {
            'pat_type_cn': 1,
            'bad_check_yn': 0,
            'app_flags': 0,
            'comp_cn': 0,
            'status_cn': 0,
        }

    @mapping
    @changed_by('safety_cap_yn')
    def no_safety_caps_yn(self, record):
        return {'no_safety_caps_yn': not record.safety_cap_yn}


@carepoint
class MedicalPatientExporter(CarepointExporter):
    _model_name = ['carepoint.medical.patient']
    _base_mapper = MedicalPatientExportMapper

    def _after_export(self):
        self.env['carepoint.address.patient']._get_by_partner(
            self.binding_record.commercial_partner_id,
            edit=True,
            recurse=True,
        )
        self.env['carepoint.account']._get_by_patient(
            self.binding_record.odoo_id,
            create=True,
            recurse=True,
        )
