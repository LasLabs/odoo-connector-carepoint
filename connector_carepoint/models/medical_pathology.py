# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.connector import ConnectorUnit
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               )
from ..unit.backend_adapter import CarepointAdapter
from ..unit.mapper import PartnerImportMapper, trim
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

from ..connector import add_checkpoint


_logger = logging.getLogger(__name__)


class MedicalPathology(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'medical.pathology'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.pathology',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointMedicalPathology(models.Model):
    """ Binding Model for the Carepoint Store """
    _name = 'carepoint.medical.pathology'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.pathology': 'odoo_id'}
    _description = 'Carepoint Pathologies'
    _cp_lib = 'pathology'

    odoo_id = fields.Many2one(
        comodel_name='medical.pathology',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class MedicalPathologyAdapter(CarepointAdapter):
    """ Backend Adapter for the Carepoint Store """
    _model_name = 'carepoint.medical.pathology'


class MedicalPathologyBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Stores.
    For every company in the list, a delayed job is created.
    """
    _model_name = ['carepoint.medical.pathology']


class MedicalPathologyUnit(ConnectorUnit):
    _model_name = 'carepoint.medical.pathology'

    def _import_by_code(self, code):
        adapter = self.unit_for(MedicalPathologyAdapter)
        importer = self.unit_for(MedicalPathologyImporter)
        for record in adapter.search(icd_cd=code):
            importer.run(record)


class MedicalPathologyImportMapper(PartnerImportMapper):
    _model_name = 'carepoint.medical.pathology'

    direct = [
        (trim('icd_cd'), 'code'),
        (trim('icd_desc'), 'name'),
    ]

    @mapping
    @only_create
    def odoo_id(self, record):
        """ Will bind the record on an existing record with the same name """
        code_type = self.code_type_id(record)
        record = self.env['medical.pathology'].search([
            ('code_type_id', '=', code_type['code_type_id']),
            ('code', '=', record['icd_cd'].strip()),
        ],
            limit=1,
        )
        if record:
            return {'odoo_id': record.id}

    @mapping
    def code_type_id(self, record):
        binder = self.binder_for('carepoint.medical.pathology.code.type')
        type_id = binder.to_odoo(record['icd_cd_type'].strip())
        return {'code_type_id': type_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%s,%s' % (record['icd_cd'].strip(),
                                           record['icd_cd_type'].strip(),
                                           )}


class MedicalPathologyImporter(CarepointImporter):
    _model_name = ['carepoint.medical.pathology']
    _base_mapper = MedicalPathologyImportMapper

    def _import_dependencies(self):
        record = self.carepoint_record
        self._import_dependency(record['icd_cd_type'].strip(),
                                'carepoint.medical.pathology.code.type')

    def _create(self, data):   # pragma: no cover
        binding = super(MedicalPathologyImporter, self)._create(data)
        add_checkpoint(
            self.session, binding._name, binding.id, binding.backend_id.id
        )
        return binding
