# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               )
from ..unit.backend_adapter import CarepointAdapter
from ..unit.mapper import (CarepointImportMapper,
                           trim,
                           )
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class MedicalMedicamentAttribute(models.Model):
    _inherit = 'medical.medicament.attribute'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.medicament.attribute',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointMedicalMedicamentAttribute(models.Model):
    _name = 'carepoint.medical.medicament.attribute'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.medicament.attribute': 'odoo_id'}
    _description = 'Carepoint Medical Medicament Attribute'
    _cp_lib = 'fdb_attr'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='MedicalMedicamentAttribute',
        comodel_name='medical.medicament.attribute',
        required=True,
        ondelete='restrict'
    )


class MedicalMedicamentAttributeAdapter(CarepointAdapter):
    _model_name = 'carepoint.medical.medicament.attribute'


class MedicalMedicamentAttributeBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint MedicalMedicamentAttributes.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.medical.medicament.attribute']


class MedicalMedicamentAttributeImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.medical.medicament.attribute'
    direct = [
        (trim('IPTDESC'), 'name'),
    ]

    @mapping
    @only_create
    def attribute_type_id(self, record):
        binder = self.binder_for('medical.medicament.attribute.type')
        attribute_type_id = binder.to_odoo(record['IPTCATID'])
        return {'attribute_type_id': attribute_type_id.id}

    @mapping
    def carepoint_id(self, record):
        # @TODO: Handle for dual PK on IPTCATID
        return {'carepoint_id': record['IPTDESCID']}


class MedicalMedicamentAttributeImporter(CarepointImporter):
    _model_name = ['carepoint.medical.medicament.attribute']
    _base_mapper = MedicalMedicamentAttributeImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['IPCATID'],
                                'medical.medicament.attribute.type')
