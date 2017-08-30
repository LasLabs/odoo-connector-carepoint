# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.connector import ConnectorUnit
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               )
from ..unit.backend_adapter import CarepointAdapter
from ..unit.mapper import BaseImportMapper
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

from .fdb_img_date import FdbImgDateUnit


_logger = logging.getLogger(__name__)


class FdbImgId(models.Model):
    _inherit = 'fdb.img.id'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.img.id',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointFdbImgId(models.Model):
    _name = 'carepoint.fdb.img.id'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.img.id': 'odoo_id'}
    _description = 'Carepoint FdbImgId'
    _cp_lib = 'fdb_img_id'

    odoo_id = fields.Many2one(
        string='FdbImgId',
        comodel_name='fdb.img.id',
        required=True,
        ondelete='restrict'
    )


class FdbImgIdAdapter(CarepointAdapter):
    _model_name = 'carepoint.fdb.img.id'


class FdbImgIdUnit(ConnectorUnit):
    _model_name = 'carepoint.fdb.img.id'

    def _import_by_ndc(self, ndc):
        """ It should search for records w/ ndc and import
        Params:
            ndc: :type:str NDC to seartch for
        """
        adapter = self.unit_for(FdbImgIdAdapter)
        importer = self.unit_for(FdbImgIdImporter)
        for record in adapter.search(IMGNDC=ndc):
            importer.run(record)


class FdbImgIdBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbImgIds.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.img.id']


class FdbImgIdImportMapper(BaseImportMapper):
    _model_name = 'carepoint.fdb.img.id'

    direct = [
        ('IMGDFID', 'df_id'),
    ]

    @mapping
    @only_create
    def ndc_id(self, record):
        binder = self.binder_for('carepoint.fdb.ndc')
        ndc_id = binder.to_odoo(record['IMGNDC'].strip())
        return {'ndc_id': ndc_id}

    @mapping
    @only_create
    def manufacturer_id(self, record):
        binder = self.binder_for('carepoint.fdb.img.mfg')
        mfg_id = binder.to_odoo(record['IMGMFGID'])
        return {'manufacturer_id': mfg_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['IMGUNIQID']}


class FdbImgIdImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.img.id']
    _base_mapper = FdbImgIdImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['IMGNDC'].strip(),
                                'carepoint.fdb.ndc')
        self._import_dependency(record['IMGMFGID'],
                                'carepoint.fdb.img.mfg')

    def _after_import(self, binding):
        img_unit = self.unit_for(
            FdbImgDateUnit,
            model='carepoint.fdb.img.date',
        )
        img_unit._import_by_unique_id(
            self.carepoint_record['IMGUNIQID'],
        )
