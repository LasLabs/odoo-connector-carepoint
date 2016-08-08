# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper, trim
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


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
