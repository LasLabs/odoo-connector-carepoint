# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               )
from ..unit.backend_adapter import CarepointAdapter
from ..unit.mapper import (BaseImportMapper,
                           trim,
                           trim_and_titleize,
                           )
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class FdbRoute(models.Model):
    _inherit = 'fdb.route'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.route',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


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


class FdbRouteAdapter(CarepointAdapter):
    _model_name = 'carepoint.fdb.route'


class FdbRouteBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbRoutes.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.route']


class FdbRouteImportMapper(BaseImportMapper):
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
            '|',
            ('code', '=', record['gcrt2'].strip()),
            ('name', '=', record['gcrt_desc'].title().strip()),
        ],
            limit=1,
        )
        if route_id:
            return {'route_id': route_id.id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['gcrt'].strip()}


class FdbRouteImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.route']
    _base_mapper = FdbRouteImportMapper
