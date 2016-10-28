# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper, trim
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class FdbPemMoe(models.Model):
    _inherit = 'fdb.pem.moe'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.pem.moe',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


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
