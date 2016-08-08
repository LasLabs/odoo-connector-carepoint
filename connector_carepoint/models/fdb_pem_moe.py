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
from ..connector import get_environment
from ..unit.mapper import CarepointImportMapper, trim
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

_logger = logging.getLogger(__name__)


class CarepointFdbPemMoe(models.Model):
    _name = 'carepoint.fdb.pem.moe'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.pem.moe': 'odoo_id'}
    _description = 'Carepoint FdbPemMoe'
    _cp_lib = 'fdb_pem_moe'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbPemMoe',
        comodel_name='fdb.pem.moe',
        required=True,
        ondelete='restrict'
    )


class FdbPemMoe(models.Model):
    _inherit = 'fdb.pem.moe'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.pem.moe',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbPemMoeAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.pem.moe'


@carepoint
class FdbPemMoeBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbPemMoes.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.pem.moe']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbPemMoeImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.pem.moe'

    direct = [
        ('pemono_sn', 'pemono_sn'),
        (trim('pemtxtei'), 'pemtxtei'),
        (trim('pemtxte'), 'pemtxte'),
        (trim('pemgndr'), 'pemgndr'),
        (trim('pemage'), 'pemage'),
        ('update_yn', 'update_yn'),
    ]

    @mapping
    def mogc_id(self, record):
        mogc_id = self.env['fdb.pem.mogc'].search([
            ('pemono', '=', record['pemono']),
        ],
            limit=1,
        )
        return {'mogc_id': mogc_id.id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%d,%d' % (record['pemono'],
                                           record['pemono_sn'],
                                           )}


@carepoint
class FdbPemMoeImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.pem.moe']

    _base_mapper = FdbPemMoeImportMapper

    def _create(self, data):
        odoo_binding = super(FdbPemMoeImporter, self)._create(data)
        checkpoint = self.unit_for(FdbPemMoeAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class FdbPemMoeAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.pem.moe record """
    _model_name = ['carepoint.fdb.pem.moe']

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.fdb')
def fdb_pem_moe_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of NDCs from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbPemMoeBatchImporter)
    importer.run(filters=filters)
