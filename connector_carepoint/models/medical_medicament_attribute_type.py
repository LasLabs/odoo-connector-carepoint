# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  ImportMapper
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (CarepointImportMapper,
                           trim,
                           trim_and_titleize,
                           to_ord,
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

class MedicalMedicamentAttributeType(models.Model):
    _inherit = 'medical.medicament.attribute.type'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.medicament.attribute.type',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
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

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


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

    def _create(self, data):
        odoo_binding = super(MedicalMedicamentAttributeTypeImporter, self)._create(data)
        checkpoint = self.unit_for(MedicalMedicamentAttributeTypeAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class MedicalMedicamentAttributeTypeAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.medical.medicament.attribute.type record """
    _model_name = ['carepoint.medical.medicament.attribute.type']
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
    importer = env.get_connector_unit(MedicalMedicamentAttributeTypeBatchImporter)
    importer.run(filters=filters)
