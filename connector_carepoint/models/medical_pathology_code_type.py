# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..backend import carepoint
from ..unit.mapper import PartnerImportMapper, trim
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )


_logger = logging.getLogger(__name__)


class CarepointMedicalPathologyCodeType(models.Model):
    """ Binding Model for the Carepoint Store """
    _name = 'carepoint.medical.pathology.code.type'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.pathology.code.type': 'odoo_id'}
    _description = 'Carepoint Pathology Code Types'
    _cp_lib = 'pathology_code_type'

    odoo_id = fields.Many2one(
        comodel_name='medical.pathology.code.type',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class MedicalPathologyCodeType(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'medical.pathology.code.type'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.pathology.code.type',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class MedicalPathologyCodeTypeAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Store """
    _model_name = 'carepoint.medical.pathology.code.type'


@carepoint
class MedicalPathologyCodeTypeBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Stores.
    For every company in the list, a delayed job is created.
    """
    _model_name = ['carepoint.medical.pathology.code.type']


@carepoint
class MedicalPathologyCodeTypeImportMapper(PartnerImportMapper):
    _model_name = 'carepoint.medical.pathology.code.type'

    direct = [
        (trim('icd_cd_type_desc'), 'name'),
    ]

    @mapping
    @only_create
    def odoo_id(self, record):
        """ Will bind the record on an existing record with the same name """
        record = self.env['medical.pathology.code.type'].search(
            [('name', 'ilike', record['icd_cd_type_desc'].strip())],
            limit=1,
        )
        if record:
            return {'odoo_id': record.id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['icd_cd_type']}


@carepoint
class MedicalPathologyCodeTypeImporter(CarepointImporter):
    _model_name = ['carepoint.medical.pathology.code.type']
    _base_mapper = MedicalPathologyCodeTypeImportMapper
