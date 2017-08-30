# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api

from odoo.addons.connector.connector import ConnectorUnit
from odoo.addons.connector.unit.mapper import (mapping,
                                               changed_by,
                                               ExportMapper,
                                               none,
                                               )
from ..unit.backend_adapter import CarepointAdapter
from ..unit.mapper import BaseImportMapper
from ..unit.mapper import trim_and_titleize
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import CarepointExporter


_logger = logging.getLogger(__name__)


class CarepointAddress(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.address'
    _description = 'Carepoint Address'

    PARTNER_ATTRS = [
        'street',
        'street2',
        'zip',
        'city',
        'state_id',
        'country_id',
    ]

    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one(
        string='State',
        comodel_name='res.country.state',
    )
    country_id = fields.Many2one(
        string='Country',
        comodel_name='res.country',
    )
    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        readonly=True,
        ondelete='cascade',
    )

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.address',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )

    @api.multi
    @api.depends('partner_id', *PARTNER_ATTRS)
    def _sync_partner(self):
        for rec_id in self:
            if not len(rec_id.partner_id):
                continue
            rec_id.partner_id.write(
                self._get_partner_sync_vals(self)
            )

    @api.model
    def _get_partner_sync_vals(self, partner):
        """ It extracts sync values from the partner or partner like record
        Params:
            parner: Recordset of partner or address
        Returns:
            ``dict`` of values for create or write
        """
        vals = {}
        for attr in self.PARTNER_ATTRS:
            val = getattr(partner, attr, False)
            if getattr(val, 'id', False):
                val = val.id
            if not val:
                val = False
            vals[attr] = val
        return vals


class CarepointCarepointAddress(models.Model):
    """ Binding Model for the Carepoint Address """
    _name = 'carepoint.carepoint.address'  # This is going to be confusing...
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.address': 'odoo_id'}
    _description = 'Carepoint Address'
    _cp_lib = 'address'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='carepoint.address',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class CarepointAddressAdapter(CarepointAdapter):
    """ Backend Adapter for the Carepoint Address """
    _model_name = 'carepoint.carepoint.address'


class CarepointAddressUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.address'

    def _import_by_filter(self, **filters):
        adapter = self.unit_for(CarepointAdapter)
        importer = self.unit_for(CarepointAddressImporter)
        rec_ids = adapter.search(**filters)
        for rec_id in rec_ids:
            importer.run(rec_id)


class CarepointAddressBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Addresss.
    For every address in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.address']


class CarepointAddressImportMapper(BaseImportMapper):
    _model_name = 'carepoint.carepoint.address'

    direct = [
        (trim_and_titleize('addr1'), 'street'),
        (trim_and_titleize('addr2'), 'street2'),
        (trim_and_titleize('city'), 'city'),
    ]

    @mapping
    def zip(self, record):
        zip_plus4 = (record['zip_plus4'] or '').strip()
        _zip = (record['zip'] or '').strip()
        if zip_plus4:
            _zip = '%s-%s' % (_zip, zip_plus4)
        return {'zip': _zip}

    @mapping
    def state_id(self, record):
        state_id = self.env['res.country.state'].search([
            ('code', '=', record['state_cd'].strip()),
        ],
            limit=1
        )
        return {
            'state_id': state_id.id,
            'country_id': state_id.country_id.id,
        }

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['addr_id']}


class CarepointAddressImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.address']
    _base_mapper = CarepointAddressImportMapper


class CarepointAddressExportMapper(ExportMapper):
    _model_name = 'carepoint.carepoint.address'

    direct = [
        (none('street'), 'addr1'),
        (none('street2'), 'addr2'),
        (none('city'), 'city'),
    ]

    @mapping
    @changed_by('state_id')
    def state_cd(self, record):
        return {'state_cd': record.state_id.code}

    @mapping
    @changed_by('zip')
    def zip_and_plus_four(self, record):
        if not record.zip:
            return
        _zip = record.zip.replace('-', '')
        if len(_zip) > 5:
            return {
                'zip': _zip[0:5],
                'zip_plus4': _zip[5:],
            }
        return {'zip': _zip}

    @mapping
    @changed_by('country_id')
    def country_cd(self, record):
        return {'country_cd': record.country_id.code}

    @mapping
    def addr_id(self, record):
        return {'addr_id': record.carepoint_id}


class CarepointAddressExporter(CarepointExporter):
    _model_name = ['carepoint.carepoint.address']
    _base_mapper = CarepointAddressExportMapper
