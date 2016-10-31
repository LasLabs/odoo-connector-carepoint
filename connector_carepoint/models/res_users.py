# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               none,
                                               changed_by,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import PersonExportMapper, PersonImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import CarepointExporter

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'res.users'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.res.users',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointResUsers(models.Model):
    """ Binding Model for the Carepoint Users """
    _name = 'carepoint.res.users'
    _inherit = 'carepoint.binding'
    _inherits = {'res.users': 'odoo_id'}
    _description = 'Carepoint User'
    _cp_lib = 'user'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=True,
        ondelete='cascade'
    )


@carepoint
class ResUsersAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint User """
    _model_name = 'carepoint.res.users'


@carepoint
class ResUsersBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Users.
    For every user in the list, a delayed job is created.
    """
    _model_name = ['carepoint.res.users']


@carepoint
class ResUsersImportMapper(PersonImportMapper):
    _model_name = 'carepoint.res.users'

    direct = [
        ('login_name', 'login'),
        ('email', 'email'),
        ('job_title_lu', 'function'),
        ('user_id', 'carepoint_id'),
    ]

    @mapping
    @only_create
    def employee(self, record):
        return {'employee': True}

    @mapping
    @only_create
    def odoo_id(self, record):
        """ Will bind the user on a existing user with the same name """
        name = '%s %s' % (record['fname'], record['lname'])
        user_id = self.env['res.users'].search([
            ('name', '=ilike', name),
        ],
            limit=1,
        )
        if user_id:
            return {'odoo_id': user_id.id}


@carepoint
class ResUsersImporter(CarepointImporter):
    _model_name = ['carepoint.res.users']
    _base_mapper = ResUsersImportMapper


@carepoint
class ResUsersExportMapper(PersonExportMapper):
    _model_name = 'carepoint.res.users'

    direct = [
        (none('email'), 'email'),
        (none('function'), 'job_title_lu'),
        ('login', 'login_name'),
    ]

    @mapping
    def static_defaults(self, record):
        """ It provides all static default mappings """
        return {
            'user_type_cd': 'U',
        }


@carepoint
class ResUsersExporter(CarepointExporter):
    _model_name = ['carepoint.res.users']
    _base_mapper = ResUsersExportMapper
