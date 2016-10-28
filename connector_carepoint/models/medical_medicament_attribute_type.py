# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (CarepointImportMapper,
                           trim,
                           )
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class MedicalMedicamentAttributeType(models.Model):
    _inherit = 'medical.medicament.attribute.type'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.medicament.attribute.type',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointMedicalMedicamentAttributeType(models.Model):
    _name = 'carepoint.medical.medicament.attribute.type'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.medicament.attribute.type': 'odoo_id'}
    _description = 'Carepoint MedicalMedicament Attribute Type'
    _cp_lib = 'fdb_attr_type'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='MedicalMedicamentAttributeType',
        comodel_name='medical.medicament.attribute.type',
        required=True,
        ondelete='restrict'
    )


@carepoint
class MedicalMedicamentAttributeTypeAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.medical.medicament.attribute.type'


@carepoint
class MedicalMedicamentAttributeTypeBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint MedicalMedicamentAttributeTypes.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.medical.medicament.attribute.type']


@carepoint
class MedicalMedicamentAttributeTypeImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.medical.medicament.attribute.type'
    direct = [
        (trim('IPTCATDESC'), 'name'),
    ]

    @mapping
    def carepoint_id(self, record):
        # @TODO: Handle for dual PK on IPTCATID
        return {'carepoint_id': record['IPTCATID']}


@carepoint
class MedicalMedicamentAttributeTypeImporter(CarepointImporter):
    _model_name = ['carepoint.medical.medicament.attribute.type']
    _base_mapper = MedicalMedicamentAttributeTypeImportMapper
