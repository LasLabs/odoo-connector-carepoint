# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (CarepointImportMapper,
                           trim,
                           trim_and_titleize,
                           )
from ..connector import get_environment
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in xrange(0, len(items), length):
        yield items[index:index + length]


class CarepointFdbForm(models.Model):
    _name = 'carepoint.fdb.form'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.form': 'odoo_id'}
    _description = 'Carepoint FdbForm'
    _cp_lib = 'fdb_form'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbForm',
        comodel_name='fdb.form',
        required=True,
        ondelete='restrict'
    )


class FdbForm(models.Model):
    _inherit = 'fdb.form'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.form',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbFormAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.form'


@carepoint
class FdbFormBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbForms.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.form']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbFormImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.form'
    direct = [
        (trim('gcdf'), 'gcdf'),
        (trim('dose'), 'code'),
        (trim_and_titleize('gcdf_desc'), 'name'),
        ('update_yn', 'update_yn'),
    ]

    @mapping
    @only_create
    def form_id(self, record):
        """ Will bind the form on a existing form with same name """
        form_id = self.env['medical.drug.form'].search([
            '|',
            ('code', '=', record['dose'].strip()),
            ('name', '=', record['gcdf_desc'].strip().title()),
        ],
            limit=1,
        )
        if form_id:
            return {'form_id': form_id.id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['dose'].strip()}


@carepoint
class FdbFormImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.form']
    _base_mapper = FdbFormImportMapper


@job(default_channel='root.carepoint.fdb')
def fdb_form_import_batch(session, model_name, backend_id,
                          filters=None
                          ):
    """ Prepare the import of Forms from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbFormBatchImporter)
    importer.run(filters=filters)
