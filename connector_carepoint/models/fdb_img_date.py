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


class CarepointFdbImgDate(models.Model):
    _name = 'carepoint.fdb.img.date'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.img.date': 'odoo_id'}
    _description = 'Carepoint FdbImgDate'
    _cp_lib = 'fdb_img_date'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbImgDate',
        comodel_name='fdb.img.date',
        required=True,
        ondelete='restrict'
    )


class FdbImgDate(models.Model):
    _inherit = 'fdb.img.date'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.img.date',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbImgDateAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.img.date'


@carepoint
class FdbImgDateBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbImgDates.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.img.date']


@carepoint
class FdbImgDateImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.img.date'
    direct = [
        ('IMGSTRTDT', 'start_date'),
        ('IMGSTOPDT', 'stop_date'),
        ('IMGID', 'img_id'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['IMGUNIQID']}


@carepoint
class FdbImgDateImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.img.date']
    _base_mapper = FdbImgDateImportMapper
