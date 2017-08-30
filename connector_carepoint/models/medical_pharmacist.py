# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               none,
                                               )
from ..unit.backend_adapter import CarepointAdapter
from ..unit.mapper import (PersonImportMapper,
                           PersonExportMapper,
                           CommonDateImporterMixer,
                           trim,
                           )
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import CarepointExporter


_logger = logging.getLogger(__name__)


class MedicalPharmacist(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'medical.pharmacist'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.pharmacist',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointMedicalPharmacist(models.Model):
    """ Binding Model for the Carepoint Pharmacists """
    _name = 'carepoint.medical.pharmacist'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.pharmacist': 'odoo_id'}
    _description = 'Carepoint Pharmacist'
    _cp_lib = 'doctor'

    odoo_id = fields.Many2one(
        comodel_name='medical.pharmacist',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class MedicalPharmacistAdapter(CarepointAdapter):
    """ Backend Adapter for the Carepoint Pharmacist """
    _model_name = 'carepoint.medical.pharmacist'


class MedicalPharmacistBatchImporter(DelayedBatchImporter,
                                     CommonDateImporterMixer):
    """ Import the Carepoint Pharmacists.
    For every pharmacist in the list, a delayed job is created.
    """
    _model_name = ['carepoint.medical.pharmacist']


class MedicalPharmacistImportMapper(PersonImportMapper):
    _model_name = 'carepoint.medical.pharmacist'

    direct = [
        (trim('fname'), 'firstname'),
        (trim('lname'), 'lastname'),
        (trim('email'), 'email'),
        ('user_id', 'carepoint_id'),
    ]

    @mapping
    @only_create
    def partner_id(self):
        """ Will bind the pharmacist to the partner of the user. """
        binder = self.binder_for('carepoint.res.users')
        user = binder.to_odoo(record['user_id'], browse=True)
        return {
            'partner_id': user.partner_id.id,
        }


class MedicalPharmacistImporter(CarepointImporter,
                                CommonDateImporterMixer):
    _model_name = ['carepoint.medical.pharmacist']
    _base_mapper = MedicalPharmacistImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['user_id'],
                                'carepoint.res.users')
