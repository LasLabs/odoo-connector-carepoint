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


class CarepointFdbGcn(models.Model):
    _name = 'carepoint.fdb.gcn'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.gcn': 'odoo_id'}
    _description = 'Carepoint FdbGcn'
    _cp_lib = 'fdb_gcn'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbGcn',
        comodel_name='fdb.gcn',
        required=True,
        ondelete='restrict'
    )


class FdbGcn(models.Model):
    _inherit = 'fdb.gcn'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.gcn',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbGcnAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.gcn'


@carepoint
class FdbGcnBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbGcns.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.gcn']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbGcnImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.gcn'
    direct = [
        ('gcn_seqno', 'name'),
        ('update_yn', 'update_yn'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['gcn_seqno']}


@carepoint
class FdbGcnImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.gcn']

    _base_mapper = FdbGcnImportMapper

    def _create(self, data):
        odoo_binding = super(FdbGcnImporter, self)._create(data)
        checkpoint = self.unit_for(FdbGcnAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['gcn_seqno'],
                                'carepoint.fdb.gcn.seq')

    def _after_import(self, binding):
        self._import_dependency(self.carepoint_record['gcn_seqno'],
                                'carepoint.fdb.pem.mogc')


@carepoint
class FdbGcnAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.gcn record """
    _model_name = ['carepoint.fdb.gcn']

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
    importer = env.get_connector_unit(FdbGcnBatchImporter)
    importer.run(filters=filters)
