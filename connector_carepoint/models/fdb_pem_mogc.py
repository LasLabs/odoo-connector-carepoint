# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector_v9.unit.mapper import mapping
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import BaseImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        import_record,
                                        )
from .fdb_pem_moe import FdbPemMoeAdapter

_logger = logging.getLogger(__name__)


class FdbPemMogc(models.Model):
    _inherit = 'fdb.pem.mogc'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.pem.mogc',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointFdbPemMogc(models.Model):
    _name = 'carepoint.fdb.pem.mogc'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.pem.mogc': 'odoo_id'}
    _description = 'Carepoint FdbPemMogc'
    _cp_lib = 'fdb_pem_mogc'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbPemMogc',
        comodel_name='fdb.pem.mogc',
        required=True,
        ondelete='restrict'
    )


@carepoint
class FdbPemMogcAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.pem.mogc'


@carepoint
class FdbPemMogcBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbPemMogcs.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.pem.mogc']


@carepoint
class FdbPemMogcImportMapper(BaseImportMapper):
    _model_name = 'carepoint.fdb.pem.mogc'

    direct = [
        ('update_yn', 'update_yn'),
        ('pemono', 'pemono'),
    ]

    @mapping
    def gcn_ids(self, record):
        binder = self.binder_for('carepoint.fdb.gcn')
        gcn_id = binder.to_odoo(record['gcn_seqno'])
        return {'gcn_ids': [(4, gcn_id)]}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['gcn_seqno']}


@carepoint
class FdbPemMogcImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.pem.mogc']
    _base_mapper = FdbPemMogcImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['gcn_seqno'],
                                'carepoint.fdb.gcn')

    def _after_import(self, binding):
        pem_adapter = self.unit_for(
            FdbPemMoeAdapter, model='carepoint.fdb.pem.moe',
        )
        record = self.carepoint_record
        domain = {'pemono': record['pemono']}
        attributes = ['pemono', 'pemono_sn']
        for rec_id in pem_adapter.search_read(attributes, **domain):
            import_record.delay(
                self.session,
                'carepoint.fdb.pem.moe',
                self.backend_record.id,
                '{0},{1}'.format(rec_id['pemono'], rec_id['pemono_sn']),
                force=True,
            )
