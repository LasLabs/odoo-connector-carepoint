# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, _
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               ExportMapper,
                                               )
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import CarepointImporter
from ..unit.export_synchronizer import CarepointExporter

from .phone import CarepointPhone

from ..connector import add_checkpoint

_logger = logging.getLogger(__name__)

try:
    from carepoint.models.phone_mixin import EnumPhoneType
except ImportError:
    _logger.warning('Cannot import EnumPhoneType from carepoint')


class CarepointPhoneAbstract(models.AbstractModel):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherits = {'carepoint.phone': 'phone_id'}
    _name = 'carepoint.phone.abstract'
    _description = 'Carepoint Phone Abstract'

    phone_id = fields.Many2one(
        string='Phone',
        comodel_name='carepoint.phone',
        required=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        required=True,
        store=True,
        compute='_compute_partner_id',
        inverse='_set_partner_id',
    )
    res_model = fields.Char(
        string='Resource Model',
        default=lambda s: s._default_res_model(),
    )
    res_id = fields.Integer(
        string='Resource PK',
        compute='_compute_res_id',
        store=True,
    )

    @property
    @api.multi
    def medical_entity_id(self):
        self.ensure_one()
        return self.env[self.res_model].browse(self.res_id)

    @api.model
    def _default_res_model(self):
        """ It returns the res model. Should be overloaded in children """
        raise NotImplementedError(
            _('_default_res_model should be implemented in child classes')
        )

    @api.multi
    def _compute_partner_id(self):
        """ It sets the partner_id from the phone_id """
        for rec_id in self:
            rec_id.partner_id = rec_id.phone_id.partner_id.id

    @api.multi
    @api.depends(
        'partner_id',
        *['partner_id.%s' % a for a in CarepointPhone.PARTNER_ATTRS]
    )
    def _set_partner_id(self):
        """ It sets the partner_id and attrs on the phone_id """
        for rec_id in self:
            rec_id.phone_id.write({
                'partner_id': rec_id.partner_id.id,
                'phone': rec_id.partner_id[rec_id.partner_field_name]
            })

    @api.multi
    @api.depends('partner_id', 'res_model')
    def _compute_res_id(self):
        """ It computes the resource ID from model """
        for rec_id in self:
            if not all([rec_id.res_model, rec_id.partner_id]):
                continue
            medical_entity = self.env[rec_id.res_model].search([
                ('partner_id', '=', rec_id.partner_id.id),
            ],
                limit=1,
            )
            rec_id.res_id = medical_entity.id

    @api.model
    def _get_by_partner(self, partner, edit=True, recurse=False):
        """ It returns the phone associated to the partner.
        Params:
            partner: Recordset singleton of partner to search for
            edit: Bool determining whether to create new or edit existing
                phone
            recurse: Bool determining whether to recurse into children (this
                is only functional when edit=True)
        Return:
            Recordset of partner phone
        """
        phones = self.search([('partner_id', '=', partner.id)])
        partner_vals = self.phone_id._get_partner_sync_vals(partner)
        _logger.debug(
            '_get_by_partner %s, %s, %s', phones, partner, partner_vals,
        )
        if not edit:
            return phones
        for phone in phones:
            phone.write({
                'phone': partner_vals[phone.partner_field_name],
            })
            del partner_vals[phone.partner_field_name]
        for name, val in partner_vals.iteritems():
            phones += self.create({
                'partner_id': partner.id,
                'partner_field_name': name,
                'phone': val,
            })
        if recurse:
            for child in partner.child_ids:
                self._get_by_partner(child, edit, recurse)
        return phones


@carepoint
class CarepointPhoneAbstractImportMapper(CarepointImportMapper):

    # It provides a mapping for Carepoint Phone Types to Odoo
    #   @TODO: Figure out a way to support all the types & prioritize
    PHONE_MAP = {
        'business': 'phone',
        'mobile': 'mobile',
        'home': 'phone',
        'business_fax': 'fax',
        'home_fax': 'fax',
    }

    def partner_id(self, record, medical_entity):
        """ It returns either the existing partner or a new one
        Params:
            record: ``dict`` of carepoint record
            medical_entity: Recordset with a ``partner_id`` column
        Return:
            ``dict`` of values for mapping
        """
        partner = medical_entity.partner_id
        return {'partner_id': partner.id}

    def res_model_and_id(self, record, medical_entity):
        """ It returns the vals dict for res_model and res_id
        Params:
            record: ``dict`` of carepoint record
            medical_entity: Recordset with a ``partner_id`` column
        Return:
            ``dict`` of values for mapping
        """
        return {
            'res_id': medical_entity.id,
            'res_model': medical_entity._name,
        }

    @mapping
    def partner_field_name(self, record):
        """ It determines what type of phone number this is """
        phone_type = EnumPhoneType(record['phone_type_cn'])
        try:
            return {'partner_field_name': self.PHONE_MAP[phone_type.name]}
        except KeyError:
            _logger.warning(_('Cannot find a phone type for "%s"'),
                            phone_type.name,
                            )
            return

    @mapping
    @only_create
    def phone_id(self, record):
        binder = self.binder_for('carepoint.carepoint.phone')
        phone_id = binder.to_odoo(record['phone_id'])
        return {'phone_id': phone_id}


@carepoint
class CarepointPhoneAbstractImporter(CarepointImporter):
    _model_name = 'carepoint.phone.abstract'

    def _import_dependencies(self):
        """ Import depends for record """
        self._import_dependency(self.carepoint_record['phone_id'],
                                'carepoint.carepoint.phone')

    def _create(self, data):  # pragma: no cover
        binding = super(CarepointPhoneAbstractImporter, self)._create(data)
        add_checkpoint(
            self.session, binding._name, binding.id, binding.backend_id.id
        )
        return binding


@carepoint
class CarepointPhoneAbstractExportMapper(ExportMapper):

    PHONE_MAP = {
        'phone': 'business',
        'mobile': 'mobile',
        'fax': 'business_fax',
    }

    @mapping
    def phone_id(self, binding):
        binder = self.binder_for('carepoint.carepoint.phone')
        rec_id = binder.to_backend(binding.phone_id.id)
        return {'phone_id': rec_id}

    def _get_phone_type(self, field_name):
        try:
            return EnumPhoneType[
                self.PHONE_MAP.get(field_name, 'business')
            ]
        except KeyError:
            _logger.warning(
                _('Cannot find phone type for field name "%s"'),
                field_name,
            )
            return

    @mapping
    def phone_type_cn(self, binding):
        phone_type = self._get_phone_type(
            binding.partner_field_name,
        )
        if phone_type:
            return {
                'phone_type_cn': phone_type.value,
            }

    @mapping
    def static_defaults(self, binding):
        return {
            'priority': 1,
            'app_flags': 0,
        }


@carepoint
class CarepointPhoneAbstractExporter(CarepointExporter):
    _model_name = 'carepoint.phone.abstract'

    def _export_dependencies(self):
        self._export_dependency(self.binding_record.phone_id,
                                'carepoint.carepoint.phone')
