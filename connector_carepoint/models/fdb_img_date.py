# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.connector import ConnectorUnit
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
    _cp_lib = 'fdb_img_date'

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
class FdbImgDateUnit(ConnectorUnit):
    _model_name = 'carepoint.fdb.img.date'

    def _import_by_unique_id(self, unique_id):
        """ It imports by CP col ``IMGUNIQID`` """
        adapter = self.unit_for(FdbImgDateAdapter)
        importer = self.unit_for(FdbImgDateImporter)
        for record in adapter.search(IMGUNIQID=unique_id):
            importer.run(record)


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
    ]

    @mapping
    def relation_id(self, record):
        binder = self.binder_for('carepoint.fdb.img.id')
        relation_id = binder.to_odoo(record['IMGUNIQID'])
        return {'relation_id': relation_id}

    @mapping
    def image_id(self, record):
        binder = self.binder_for('carepoint.fdb.img')
        img_id = binder.to_odoo(record['IMGID'])
        return {'image_id': img_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%s,%s' % (record['IMGUNIQID'],
                                           record['IMGSTRTDT'],
                                           )}


@carepoint
class FdbImgDateImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.img.date']
    _base_mapper = FdbImgDateImportMapper

    def _import_dependencies(self):
        """ It imports depends for record """
        self._import_dependency(self.carepoint_record['IMGUNIQID'],
                                'carepoint.fdb.img.id')
        self._import_dependency(self.carepoint_record['IMGID'],
                                'carepoint.fdb.img')
