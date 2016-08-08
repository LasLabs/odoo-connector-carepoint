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
from ..unit.mapper import PartnerImportMapper
from ..unit.mapper import trim_and_titleize
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in xrange(0, len(items), length):
        yield items[index:index + length]


class CarepointFdbImgMfg(models.Model):
    _name = 'carepoint.fdb.img.mfg'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.img.mfg': 'odoo_id'}
    _description = 'Carepoint FdbImgMfg'
    _cp_lib = 'fdb_img_mfg'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbImgMfg',
        comodel_name='fdb.img.mfg',
        required=True,
        ondelete='restrict'
    )


class FdbImgMfg(models.Model):
    _inherit = 'fdb.img.mfg'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.img.mfg',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
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

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbImgMfgImportMapper(PartnerImportMapper):
    _model_name = 'carepoint.fdb.img.mfg'
    direct = [
        (trim_and_titleize('IMGMFGNAME'), 'name'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['IMGMFGID']}


@carepoint
class FdbImgMfgImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.img.mfg']

    _base_mapper = FdbImgMfgImportMapper

    def _create(self, data):
        odoo_binding = super(FdbImgMfgImporter, self)._create(data)
        checkpoint = self.unit_for(FdbImgMfgAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class FdbImgMfgAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.img.mfg record """
    _model_name = ['carepoint.fdb.img.mfg']

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.fdb')
def fdb_img_mfg_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of NDCs from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbImgMfgBatchImporter)
    importer.run(filters=filters)
