# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  ImportMapper
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..connector import get_environment
from ..unit.mapper import CarepointImportMapper, trim
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in xrange(0, len(items), length):
        yield items[index:index + length]


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

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


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

    def _create(self, data):
        odoo_binding = super(FdbImgDateImporter, self)._create(data)
        checkpoint = self.unit_for(FdbImgDateAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class FdbImgDateAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.img.date record """
    _model_name = ['carepoint.fdb.img.date']
    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint')
def fdb_img_date_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of NDCs from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbImgDateBatchImporter)
    importer.run(filters=filters)
