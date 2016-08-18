# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


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
