# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (PartnerImportMapper,
                           ExportMapper,
                           trim,
                           )
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import CarepointExporter

from .address_organization import CarepointAddressOrganizationUnit
from .phone_organization import CarepointPhoneOrganizationUnit

_logger = logging.getLogger(__name__)


class CarepointCarepointOrganization(models.Model):
    """ Binding Model for the Carepoint Organization """
    _name = 'carepoint.carepoint.organization'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.organization': 'odoo_id'}
    _description = 'Carepoint Organization'
    _cp_lib = 'pharmacy'

    odoo_id = fields.Many2one(
        comodel_name='carepoint.organization',
        string='Organization',
        required=True,
        ondelete='cascade'
    )


class CarepointOrganization(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    # Cannot direct bind due to store organization sync
    _name = 'carepoint.organization'
    _inherits = {'medical.pharmacy': 'pharmacy_id'}

    pharmacy_id = fields.Many2one(
        string='Organization',
        comodel_name='medical.pharmacy',
        required=True,
        ondelete='cascade',
    )
    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.organization',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class CarepointOrganizationAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Organization """
    _model_name = 'carepoint.carepoint.organization'


@carepoint
class CarepointOrganizationBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Organizations.
    For every organization in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.organization']


@carepoint
class CarepointOrganizationImportMapper(PartnerImportMapper):
    _model_name = 'carepoint.carepoint.organization'

    direct = [
        (trim('name'), 'name'),
        (trim('url'), 'website'),
        (trim('email'), 'email'),
        (trim('phone'), 'phone'),
        (trim('fed_tax_id'), 'vat'),
        ('add_date', 'created_at'),
        ('chg_date', 'updated_at'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['org_id']}

    @mapping
    @only_create
    def odoo_id(self, record):
        """ Will bind the organization on a existing organization
        with the same name & dob """
        name = self._get_name(record)
        organization_id = self.env['carepoint.organization'].search(
            [('name', 'ilike', name)],
            limit=1,
        )
        if organization_id:
            return {'odoo_id': organization_id.id}


@carepoint
class CarepointOrganizationImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.organization']
    _base_mapper = CarepointOrganizationImportMapper

    def _after_import(self, partner_binding):
        """ Import the addresses """
        book = self.unit_for(CarepointAddressOrganizationUnit,
                             model='carepoint.carepoint.address.organization')
        book._import_addresses(self.carepoint_id, partner_binding)
        phone = self.unit_for(CarepointPhoneOrganizationUnit,
                              model='carepoint.carepoint.phone.organization')
        phone._import_phones(self.carepoint_id, partner_binding)


@carepoint
class CarepointOrganizationExportMapper(ExportMapper):
    _model_name = 'carepoint.carepoint.organization'

    direct = [
        ('name', 'name'),
        ('email', 'email'),
        ('website', 'url'),
        ('phone', 'phone'),
        ('vat', 'fed_tax_id_num'),
    ]

    @mapping
    def org_id(self, record):
        return {'org_id': record.carepoint_id}


@carepoint
class CarepointOrganizationExporter(CarepointExporter):
    _model_name = ['carepoint.carepoint.organization']
    _base_mapper = CarepointOrganizationExportMapper

    def _after_export(self):
        self.env['carepoint.address.organization']._get_by_partner(
            self.binding_record.commercial_partner_id,
            edit=True,
            recurse=True,
        )
        self.env['carepoint.phone.organization']._get_by_partner(
            self.binding_record.commercial_partner_id,
            edit=True,
            recurse=True,
        )
