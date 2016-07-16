# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..connector import get_environment
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in xrange(0, len(items), length):
        yield items[index:index + length]


class CarepointFdbImgId(models.Model):
    _name = 'carepoint.fdb.img.id'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.img.id': 'odoo_id'}
    _description = 'Carepoint FdbImgId'
    _cp_lib = 'fdb_img_id'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbImgId',
        comodel_name='fdb.img.id',
        required=True,
        ondelete='restrict'
    )


class FdbImgId(models.Model):
    _inherit = 'fdb.img.id'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.img.id',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbImgIdAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.img.id'


@carepoint
class FdbImgIdBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbImgIds.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.img.id']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbImgIdImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.img.id'
    direct = [
        ('IMGDFID', 'df_id'),
        ('IMGNDC', 'ndc'),
        ('IMGMFGID', 'mfg_id'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['IMGUNIQID']}


@carepoint
class FdbImgIdImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.img.id']

    _base_mapper = FdbImgIdImportMapper

    def _create(self, data):
        odoo_binding = super(FdbImgIdImporter, self)._create(data)
        checkpoint = self.unit_for(FdbImgIdAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class FdbImgIdAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.img.id record """
    _model_name = ['carepoint.fdb.img.id']

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.fdb')
def fdb_img_id_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of NDCs from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbImgIdBatchImporter)
    importer.run(filters=filters)
