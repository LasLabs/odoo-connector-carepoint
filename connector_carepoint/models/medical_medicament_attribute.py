# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (CarepointImportMapper,
                           trim,
                           )
from ..connector import get_environment
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in xrange(0, len(items), length):
        yield items[index:index + length]


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


class MedicalMedicamentAttribute(models.Model):
    _inherit = 'medical.medicament.attribute'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.medicament.attribute',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class MedicalMedicamentAttributeAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.medical.medicament.attribute'


@carepoint
class MedicalMedicamentAttributeBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint MedicalMedicamentAttributes.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.medical.medicament.attribute']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
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


@carepoint
class MedicalMedicamentAttributeImporter(CarepointImporter):
    _model_name = ['carepoint.medical.medicament.attribute']

    _base_mapper = MedicalMedicamentAttributeImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['IPCATID'],
                                'medical.medicament.attribute.type')

    def _create(self, data):
        odoo_binding = super(
            MedicalMedicamentAttributeImporter, self)._create(data)
        checkpoint = self.unit_for(MedicalMedicamentAttributeAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class MedicalMedicamentAttributeAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the
    carepoint.medical.medicament.attribute record
    """
    _model_name = ['carepoint.medical.medicament.attribute']

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.fdb')
def fdb_form_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of Forms from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(MedicalMedicamentAttributeBatchImporter)
    importer.run(filters=filters)
