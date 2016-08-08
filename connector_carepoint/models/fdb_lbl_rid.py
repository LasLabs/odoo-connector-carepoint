# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
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


class CarepointFdbLblRid(models.Model):
    _name = 'carepoint.fdb.lbl.rid'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.lbl.rid': 'odoo_id'}
    _description = 'Carepoint FdbLblRid'
    _cp_lib = 'fdb_lbl_rid'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbLblRid',
        comodel_name='fdb.lbl.rid',
        required=True,
        ondelete='restrict'
    )


class FdbLblRid(models.Model):
    _inherit = 'fdb.lbl.rid'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.lbl.rid',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbLblRidAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.lbl.rid'


@carepoint
class FdbLblRidBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbLblRids.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.lbl.rid']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbLblRidImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.lbl.rid'
    direct = [
        (trim('mfg'), 'mfg'),
        ('update_yn', 'update_yn'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['lblrid']}


@carepoint
class FdbLblRidImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.lbl.rid']

    _base_mapper = FdbLblRidImportMapper

    def _create(self, data):
        odoo_binding = super(FdbLblRidImporter, self)._create(data)
        checkpoint = self.unit_for(FdbLblRidAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class FdbLblRidAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.lbl.rid record """
    _model_name = ['carepoint.fdb.lbl.rid']

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.fdb')
def fdb_lbl_rid_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of NDCs from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbLblRidBatchImporter)
    importer.run(filters=filters)
