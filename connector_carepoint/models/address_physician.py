# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )


_logger = logging.getLogger(__name__)


class CarepointCarepointAddressPhysician(models.Model):
    """ Binding Model for the Carepoint Address Physician """
    _name = 'carepoint.carepoint.address.physician'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.address.physician': 'odoo_id'}
    _description = 'Carepoint Address Physician Many2Many Rel'
    _cp_lib = 'doctor_address'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='carepoint.address.physician',
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
         'A Carepoint binding for this address already exists.'),
    ]


class CarepointAddressPhysician(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherits = {'carepoint.address': 'address_id'}
    _name = 'carepoint.address.physician'
    _description = 'Carepoint Address Physician'

    address_id = fields.Many2one(
        string='Address',
        comodel_name='carepoint.address',
        required=True,
        ondelete='cascade',
    )
    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.address.physician',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class CarepointAddressPhysicianAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Address Physician """
    _model_name = 'carepoint.carepoint.address.physician'


@carepoint
class CarepointAddressPhysicianBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Address Physicians.
    For every address in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.address.physician']


@carepoint
class CarepointAddressPhysicianImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.carepoint.address.physician'

    @mapping
    @only_create
    def parent_id(self, record):
        binder = self.binder_for('carepoint.medical.physician')
        physician_id = binder.to_odoo(record['md_id'])
        partner_id = self.env['medical.physician'].browse(
            physician_id).partner_id
        return {
            'parent_id': partner_id.id,
        }

    @mapping
    @only_create
    def partner_and_address_id(self, record):
        binder = self.binder_for('carepoint.carepoint.address')
        address_id = binder.to_odoo(record['addr_id'])
        address_id = self.env['carepoint.address'].browse(address_id)
        return {
            'partner_id': address_id.partner_id.id,
            'address_id': address_id.id,
        }

    @mapping
    def type(self, record):
        return {'type': 'delivery'}

    @mapping
    def customer(self, record):
        return {'customer': False}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%d,%d' % (record['md_id'],
                                           record['addr_id'])}


@carepoint
class CarepointAddressPhysicianImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.address.physician']
    _base_mapper = CarepointAddressPhysicianImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['addr_id'],
                                'carepoint.carepoint.address')
