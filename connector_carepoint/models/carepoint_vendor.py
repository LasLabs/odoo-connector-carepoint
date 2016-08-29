# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  changed_by,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (PersonImportMapper,
                           PersonExportMapper,
                           trim,
                           )
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import (CarepointExporter)


_logger = logging.getLogger(__name__)


class CarepointCarepointVendor(models.Model):
    """ Binding Model for the Carepoint Vendor """
    _name = 'carepoint.carepoint.vendor'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.vendor': 'odoo_id'}
    _description = 'Carepoint Vendor'
    _cp_lib = 'VEND'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='carepoint.vendor',
        string='Vendor',
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


class CarepointVendor(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.vendor'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        ondelete='cascade',
        required=True,
    )
    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.vendor',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class CarepointVendorAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Vendor """
    _model_name = 'carepoint.carepoint.vendor'


@carepoint
class CarepointVendorBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Vendors.
    For every patient in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.vendor']


@carepoint
class CarepointVendorImportMapper(PersonImportMapper):
    _model_name = 'carepoint.carepoint.vendor'

    direct = [
        (trim('COMPANY'), 'name'),
        (trim('ADDR1'), 'street'),
        (trim('ADDR2'), 'street2'),
        (trim('CITY'), 'city'),
        (trim('ZIP'), 'zip'),
        (trim('FEDID'), 'ref'),
        (trim('phone'), 'phone'),
        (trim('fax'), 'fax'),
        ('add_date', 'created_at'),
        ('chg_date', 'updated_at'),
    ]

    @mapping
    @only_create
    def customer(self, record):
        return {'customer': False}

    @mapping
    def supplier(self, record):
        return {'supplier': True}

    @mapping
    def is_company(self, record):
        return {'is_company': True}

    @mapping
    def state_id(self, record):
        state_id = self.env['res.country.state'].search(
            [('code', '=', record['STATE'].upper())],
            limit=1,
        )
        if len(state_id):
            return {
                'state_id': state_id[0].id,
                'country_id': state_id[0].country_id.id,
            }

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['ID']}

    @mapping
    @only_create
    def odoo_id(self, record):
        """ It binds on vendor of existing name """
        vendor_id = self.env['res.partner'].search(
            [('name', 'ilike', record['COMPANY'].strip())],
            limit=1,
        )
        if len(vendor_id):
            return {'odoo_id': vendor_id[0].id}


@carepoint
class CarepointVendorImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.vendor']
    _base_mapper = CarepointVendorImportMapper


@carepoint
class CarepointVendorExportMapper(PersonExportMapper):
    _model_name = 'carepoint.carepoint.vendor'

    direct = [
        ('name', 'COMPANY'),
        ('street', 'ADDR1'),
        ('street2', 'ADDR2'),
        ('city', 'CITY'),
        ('zip', 'ZIPCODE'),
        ('ref', 'FEDID'),
        ('phone', 'PHONE'),
        ('fax', 'FAX'),
    ]

    @mapping
    @changed_by('state_id')
    def state(self, record):
        return {'STATE': record.state_id.code}


@carepoint
class CarepointVendorExporter(CarepointExporter):
    _model_name = ['carepoint.carepoint.vendor']
    _base_mapper = CarepointVendorExportMapper
