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
from ..unit.mapper import (CarepointImportMapper,
                           trim,
                           trim_and_titleize,
                           to_ord,
                          )
from ..connector import get_environment
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in xrange(0, len(items), length):
        yield items[index:index + length]


class CarepointFdbRoute(models.Model):
    _name = 'carepoint.fdb.route'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.route': 'odoo_id'}
    _description = 'Carepoint FdbRoute'
    _cp_lib = 'fdb_route'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbRoute',
        comodel_name='fdb.route',
        required=True,
        ondelete='restrict'
    )

class FdbRoute(models.Model):
    _inherit = 'fdb.route'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.route',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbRouteAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.route'


@carepoint
class FdbRouteBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbRoutes.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.route']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbRouteImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.route'
    direct = [
        (trim_and_titleize('rt'), 'rt'),
        (trim('gcrt2'), 'code'),
        (trim_and_titleize('gcrt_desc'), 'name'),
        (trim('systemic'), 'systemic'),
        ('update_yn', 'update_yn'),
    ]

    @mapping
    @only_create
    def route_id(self, record):
        """ Will bind the route on a existing route with same code """
        route_id = self.env['medical.drug.route'].search([
            ('code', '=', record['gcrt2'].strip()),
        ],
            limit=1,
        )
        if route_id:
            return {'route_id': route_id.id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['gcrt'].strip()}


@carepoint
class FdbRouteImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.route']

    _base_mapper = FdbRouteImportMapper

    def _create(self, data):
        odoo_binding = super(FdbRouteImporter, self)._create(data)
        checkpoint = self.unit_for(FdbRouteAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class FdbRouteAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.route record """
    _model_name = ['carepoint.fdb.route']
    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.fdb')
def fdb_route_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of Routes from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbRouteBatchImporter)
    importer.run(filters=filters)
