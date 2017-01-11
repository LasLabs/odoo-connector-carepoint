# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class FdbGcn(models.Model):
    _inherit = 'fdb.gcn'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.gcn',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


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

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['gcn_seqno'],
                                'carepoint.fdb.gcn.seq')

    def _after_import(self, binding):
        try:
            self._import_dependency(self.carepoint_record['gcn_seqno'],
                                    'carepoint.fdb.pem.mogc')
        except AssertionError:
            # Does not exist in some instances.
            pass
