# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import BaseImportMapper, trim
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class FdbGcnSeq(models.Model):
    _inherit = 'fdb.gcn.seq'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.gcn.seq',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointFdbGcnSeq(models.Model):
    _name = 'carepoint.fdb.gcn.seq'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.gcn.seq': 'odoo_id'}
    _description = 'Carepoint FdbGcnSeq'
    _cp_lib = 'fdb_gcn_seq'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbGcnSeq',
        comodel_name='fdb.gcn.seq',
        required=True,
        ondelete='restrict'
    )


@carepoint
class FdbGcnSeqAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.gcn.seq'


@carepoint
class FdbGcnSeqBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbGcnSeqs.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.gcn.seq']


@carepoint
class FdbGcnSeqImportMapper(BaseImportMapper):
    _model_name = 'carepoint.fdb.gcn.seq'
    direct = [
        ('gcn_seqno', 'gcn_seqno'),
        (trim('hic3'), 'hic3'),
        ('hicl_seqno', 'hicl_seqno'),
        (trim('str'), 'str'),
        ('gtc', 'gtc'),
        ('tc', 'tc'),
        ('dcc', 'dcc'),
        ('gcnseq_gi', 'gcnseq_gi'),
        ('gender', 'gender'),
        ('hic3_seqn', 'hic3_seqn'),
        (trim('str60'), 'str60'),
        ('update_yn', 'update_yn'),
    ]

    @mapping
    def form_id(self, record):
        form_id = self.env['fdb.form'].search(
            [('gcdf', '=', record['gcdf'].strip())], limit=1
        )
        return {'form_id': form_id.id}

    @mapping
    def route_id(self, record):
        binder = self.binder_for('carepoint.fdb.route')
        route_id = binder.to_odoo(record['gcrt'].strip())
        return {'route_id': route_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['gcn_seqno']}


@carepoint
class FdbGcnSeqImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.gcn.seq']
    _base_mapper = FdbGcnSeqImportMapper
