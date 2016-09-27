# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
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


_logger = logging.getLogger(__name__)


class CarepointMedicalPhysician(models.Model):
    """ Binding Model for the Carepoint Physicians """
    _name = 'carepoint.medical.physician'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.physician': 'odoo_id'}
    _description = 'Carepoint Physician'
    _cp_lib = 'doctor'

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
        (trim('state_lic_id'), 'license_num'),
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
            ('email', 'ilike', record['email']),
        ],
            limit=1,
        )
        if physician_id:
            return {'odoo_id': physician_id.id}


@carepoint
class MedicalPhysicianImporter(CarepointImporter):
    _model_name = ['carepoint.medical.physician']
    _base_mapper = MedicalPhysicianImportMapper


@carepoint
class MedicalPhysicianExportMapper(PersonExportMapper):
    _model_name = 'carepoint.medical.physician'

    direct = [
        (none('email'), 'email'),
        (none('website'), 'url'),
        (none('dea_num'), 'dea_no'),
        (none('vat'), 'fed_tax_id'),
        (none('license_num'), 'state_lic_id'),
        (none('npi_num'), 'npi_id'),
    ]


@carepoint
class MedicalPhysicianExporter(CarepointExporter):
    _model_name = ['carepoint.medical.physician']
    _base_mapper = MedicalPhysicianExportMapper

    def _after_export(self):
        self.env['carepoint.address.physician']._get_by_partner(
            self.binding_record.commercial_partner_id,
            edit=True,
            recurse=True,
        )
