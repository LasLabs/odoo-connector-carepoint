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
from ..unit.mapper import CarepointImportMapper, trim
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


class CarepointFdbNdcCsExt(models.Model):
    _name = 'carepoint.fdb.ndc.cs.ext'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.ndc.cs.ext': 'odoo_id'}
    _description = 'Carepoint FdbNdcCsExt'
    _cp_lib = 'fdb_gcn'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbNdcCsExt',
        comodel_name='fdb.ndc.cs.ext',
        required=True,
        ondelete='restrict'
    )

class FdbNdcCsExt(models.Model):
    _inherit = 'fdb.ndc.cs.ext'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.ndc.cs.ext',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbNdcCsExtAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.ndc.cs.ext'


@carepoint
class FdbNdcCsExtBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbNdcCsExts.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.ndc.cs.ext']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbNdcCsExtImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.ndc.cs.ext'
    direct = [
        (trim('gcn'), 'gcn'),
        ('update_yn', 'update_yn'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['gcn_seqno']}


@carepoint
class FdbNdcCsExtImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.ndc.cs.ext']

    _base_mapper = FdbNdcCsExtImportMapper

    def _create(self, data):
        odoo_binding = super(FdbNdcCsExtImporter, self)._create(data)
        checkpoint = self.unit_for(FdbNdcCsExtAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class FdbNdcCsExtAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.ndc.cs.ext record """
    _model_name = ['carepoint.fdb.ndc.cs.ext']
    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.fdb')
def fdb_gcn_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of NDCs from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbNdcCsExtBatchImporter)
    importer.run(filters=filters)
