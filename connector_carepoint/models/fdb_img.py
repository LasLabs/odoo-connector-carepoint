# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..connector import get_environment
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in xrange(0, len(items), length):
        yield items[index:index + length]


class CarepointFdbImg(models.Model):
    _name = 'carepoint.fdb.img'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.img': 'odoo_id'}
    _description = 'Carepoint FdbImg'
    _cp_lib = 'fdb_img'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbImg',
        comodel_name='fdb.img',
        required=True,
        ondelete='restrict'
    )


class FdbImg(models.Model):
    _inherit = 'fdb.img'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.img',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbImgAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.img'


@carepoint
class FdbImgBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbImgs.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.img']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbImgImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.img'
    direct = [
        ('IMGFILENM', 'file_name'),
        ('data', 'data'),
    ]

    @mapping
    def data(self, record):
        return {'data': record['data'].decode('base64')}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['IMGID']}


@carepoint
class FdbImgImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.img']

    _base_mapper = FdbImgImportMapper

    def _get_carepoint_data(self):
        """ Return the raw Carepoint data for ``self.carepoint_id`` """
        _logger.debug('Getting CP data for %s', self.carepoint_id)
        record = self.backend_adapter.read(self.carepoint_id, [
            'IMGFILENM', 'IMAGE_PATH', 'IMGID'
        ])
        record['data'] = self.backend_adapter.read_image(record['IMAGE_PATH'])
        return record

    def _create(self, data):
        odoo_binding = super(FdbImgImporter, self)._create(data)
        checkpoint = self.unit_for(FdbImgAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class FdbImgAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.img record """
    _model_name = ['carepoint.fdb.img']

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.fdb')
def fdb_img_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of NDCs from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbImgBatchImporter)
    importer.run(filters=filters)
