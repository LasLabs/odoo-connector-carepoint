# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (PersonImportMapper,
                           trim,
                           )
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class CarepointMedicalPhysician(models.Model):
    """ Binding Model for the Carepoint Physicians """
    _name = 'carepoint.medical.physician'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.physician': 'odoo_id'}
    _description = 'Carepoint Physician'
    _cp_lib = 'doctor'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='medical.physician',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class MedicalPhysician(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'medical.physician'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.physician',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class MedicalPhysicianAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Physician """
    _model_name = 'carepoint.medical.physician'


@carepoint
class MedicalPhysicianBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Physicians.
    For every physician in the list, a delayed job is created.
    """
    _model_name = ['carepoint.medical.physician']


@carepoint
class MedicalPhysicianImportMapper(PersonImportMapper):
    _model_name = 'carepoint.medical.physician'

    direct = [
        (trim('email'), 'email'),
        (trim('url'), 'website'),
        (trim('dea_no'), 'dea_num'),
        (trim('fed_tax_id'), 'vat'),
        (trim('stat_lic_id'), 'license_num'),
        (trim('npi_id'), 'npi_num'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['md_id']}

    @only_create
    @mapping
    def odoo_id(self, record):
        """ Will bind the physician on a existing physician
        with the same name & email """
        name = self._get_name(record)
        physician_id = self.env['medical.physician'].search([
            ('name', 'ilike', name),
            ('email', 'ilike', record.get('email')),
        ],
            limit=1,
        )
        if physician_id:
            return {'odoo_id': physician_id.id}


@carepoint
class MedicalPhysicianImporter(CarepointImporter):
    _model_name = ['carepoint.medical.physician']
    _base_mapper = MedicalPhysicianImportMapper
