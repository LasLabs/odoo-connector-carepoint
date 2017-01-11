# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import PartnerImportMapper, trim
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class FdbImgMfg(models.Model):
    _inherit = 'fdb.img.mfg'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.img.mfg',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointFdbImgMfg(models.Model):
    _name = 'carepoint.fdb.img.mfg'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.img.mfg': 'odoo_id'}
    _description = 'Carepoint FdbImgMfg'
    _cp_lib = 'fdb_img_mfg'

    odoo_id = fields.Many2one(
        string='FdbImgMfg',
        comodel_name='fdb.img.mfg',
        required=True,
        ondelete='restrict'
    )


@carepoint
class FdbImgMfgAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.img.mfg'


@carepoint
class FdbImgMfgBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbImgMfgs.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.img.mfg']


@carepoint
class FdbImgMfgImportMapper(PartnerImportMapper):
    _model_name = 'carepoint.fdb.img.mfg'
    direct = [
        (trim('IMGMFGNAME'), 'name'),
    ]

    @mapping
    @only_create
    def manufacturer_id(self, record):
        """ It finds Manufacturer of same name and binds on it """
        manufacturer = self.env['medical.manufacturer'].search(
            [('name', 'ilike', record['IMGMFGNAME'].strip())],
            limit=1,
        )
        if len(manufacturer):
            return {'manufacturer_id': manufacturer[0].id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['IMGMFGID']}


@carepoint
class FdbImgMfgImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.img.mfg']
    _base_mapper = FdbImgMfgImportMapper
