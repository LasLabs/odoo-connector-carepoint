# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields, api

from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  changed_by,
                                                  ExportMapper,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import CarepointExporter


_logger = logging.getLogger(__name__)


try:
    import phonenumbers
except ImportError:
    _logger.warning('Cannot import phonenumbers')


class CarepointCarepointPhone(models.Model):
    """ Binding Model for the Carepoint Phone """
    _name = 'carepoint.carepoint.phone'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.phone': 'odoo_id'}
    _description = 'Carepoint Phone'
    _cp_lib = 'phone'

    odoo_id = fields.Many2one(
        comodel_name='carepoint.phone',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class CarepointPhone(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.phone'
    _description = 'Carepoint Phone'

    PARTNER_ATTRS = [
        'phone',
        'mobile',
        'fax',
    ]

    phone = fields.Char()
    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        readonly=True,
        ondelete='cascade',
    )
    partner_field_name = fields.Char(
        default='phone',
    )

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.phone',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )

    @api.multi
    def _sync_partner(self):
        for rec_id in self:
            if not rec_id.partner_id:
                continue
            field_name = rec_id.partner_field_name
            rec_id.partner_id[field_name] = rec_id.phone

    @api.model
    def _get_partner_sync_vals(self, partner):
        """ It extracts sync values from the partner or partner like record
        Params:
            parner: Recordset of partner or phone
        Returns:
            ``dict`` of values for create or write
        """
        return {attr: partner[attr] for attr in self.PARTNER_ATTRS}


@carepoint
class CarepointPhoneAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Phone """
    _model_name = 'carepoint.carepoint.phone'


@carepoint
class CarepointPhoneUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.phone'

    def _import_by_filter(self, **filters):
        adapter = self.unit_for(CarepointCRUDAdapter)
        importer = self.unit_for(CarepointPhoneImporter)
        rec_ids = adapter.search(**filters)
        for rec_id in rec_ids:
            importer.run(rec_id)


@carepoint
class CarepointPhoneBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Phones.
    For every phone in the list, a delayed job is created.
    """
    _model_name = 'carepoint.carepoint.phone'


@carepoint
class CarepointPhoneImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.carepoint.phone'

    @mapping
    def phone(self, record):
        phone_no = (record['phone_no'] or '').strip()
        area_code = (record['area_code'] or '').strip()
        ext = (record['extension'] or '').strip()
        phone = '%s-%s' % (phone_no[0:3], phone_no[3:])
        if not area_code:
            area_code = '000'
        phone = '+1 (%s) %s' % (area_code, phone)
        if ext:
            phone = '%s x%s' % (phone, ext)
        return {'phone': phone}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['phone_id']}


@carepoint
class CarepointPhoneImporter(CarepointImporter):
    _model_name = 'carepoint.carepoint.phone'
    _base_mapper = CarepointPhoneImportMapper


@carepoint
class CarepointPhoneExportMapper(ExportMapper):
    _model_name = 'carepoint.carepoint.phone'

    @mapping
    @changed_by('phone')
    def phone(self, record):
        if not record.phone:
            return
        country = record.partner_id.country_id.code or 'US'
        try:
            phone = phonenumbers.parse(record.phone, country)
        except phonenumbers.phonenumberutil.NumberParseException:
            return
        national_number = str(phone.national_number)
        vals = {
            'area_code': national_number[0:3],
            'phone_no': national_number[3:],
        }
        vals['extension'] = phone.extension or ''
        return vals

    @mapping
    def phone_id(self, record):
        return {'phone_id': record.carepoint_id}


@carepoint
class CarepointPhoneExporter(CarepointExporter):
    _model_name = ['carepoint.carepoint.phone']
    _base_mapper = CarepointPhoneExportMapper
