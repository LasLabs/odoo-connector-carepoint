# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import PersonImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class CarepointResUsers(models.Model):
    """ Binding Model for the Carepoint Users """
    _name = 'carepoint.res.users'
    _inherit = 'carepoint.binding'
    _inherits = {'res.users': 'odoo_id'}
    _description = 'Carepoint User'
    _cp_lib = 'user'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='res.users',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class MedicalUser(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'res.users'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.res.users',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class MedicalUserAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint User """
    _model_name = 'carepoint.res.users'


@carepoint
class MedicalUserBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Users.
    For every user in the list, a delayed job is created.
    """
    _model_name = ['carepoint.res.users']


@carepoint
class MedicalUserImportMapper(PersonImportMapper):
    _model_name = 'carepoint.res.users'

    direct = [
        ('login_name', 'login'),
        ('email', 'email'),
        ('job_title_lu', 'function'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['user_id']}

    @mapping
    def employee(self, record):
        return {'employee': True}

    @only_create
    @mapping
    def odoo_id(self, record):
        """ Will bind the user on a existing user
        with the same name & email """
        user_id = self.env['res.users'].search([
            ('login', 'ilike', record.get('login_name')),
        ],
            limit=1,
        )
        if user_id:
            return {'odoo_id': user_id.id}


@carepoint
class MedicalUserImporter(CarepointImporter):
    _model_name = ['carepoint.res.users']
    _base_mapper = MedicalUserImportMapper
