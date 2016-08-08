# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import PersonImportMapper
from ..connector import get_environment
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

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
    backend_id = fields.Many2one(
        comodel_name='carepoint.backend',
        string='Carepoint Backend',
        store=True,
        readonly=True,
        # override 'carepoint.binding', can't be INSERTed if True:
        required=False,
    )
    created_at = fields.Date('Created At (on Carepoint)')
    updated_at = fields.Date('Updated At (on Carepoint)')

    _sql_constraints = [
        ('odoo_uniq', 'unique(backend_id, odoo_id)',
         'A Carepoint binding for this user already exists.'),
    ]


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

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


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
        self._get_name(record)
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

    def _create(self, data):
        binding = super(MedicalUserImporter, self)._create(data)
        checkpoint = self.unit_for(MedicalUserAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    #
    # def _after_import(self, partner_binding):
    #     """ Import the addresses """
    #     book = self.unit_for(PartnerAddressBook, model='carepoint.address')
    #     book.import_addresses(self.carepoint_id, partner_binding.id)


@carepoint
class MedicalUserAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.res.users record """
    _model_name = ['carepoint.res.users', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.core')
def user_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of users modified on Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(MedicalUserBatchImporter)
    importer.run(filters=filters)
