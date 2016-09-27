# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields, api, _
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  ExportMapper,
                                                  )
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import CarepointImporter
from ..unit.export_synchronizer import CarepointExporter

from .address import CarepointAddress

from ..connector import add_checkpoint


_logger = logging.getLogger(__name__)


class CarepointAddressAbstract(models.AbstractModel):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherits = {'carepoint.address': 'address_id'}
    _name = 'carepoint.address.abstract'
    _description = 'Carepoint Address Abstract'

    address_id = fields.Many2one(
        string='Address',
        comodel_name='carepoint.address',
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
    @api.depends('partner_id')
    def _compute_partner_id(self):
        """ It sets the partner_id from the address_id """
        for rec_id in self:
            rec_id.partner_id = rec_id.address_id.partner_id.id

    @api.multi
    @api.depends(
        'partner_id',
        *['partner_id.%s' % a for a in CarepointAddress.PARTNER_ATTRS]
    )
    def _set_partner_id(self):
        """ It sets the partner_id and attrs on the address_id """
        for rec_id in self:
            need_sync = True
            if rec_id.partner_id != rec_id.address_id.partner_id:
                rec_id.address_id.write({'partner_id': rec_id.partner_id.id})
            if not CarepointAddressAbstractImportMapper._has_empty_address(
                rec_id
            ):
                vals = self.env['carepoint.address']._get_partner_sync_vals(
                    rec_id.partner_id,
                )
                if any(vals.values()):
                    need_sync = False
            if need_sync:
                rec_id.address_id._sync_partner()
            else:
                rec_id.address_id.write(vals)

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
        """ It returns the address associated to the partner.
        Params:
            partner: Recordset singleton of partner to search for
            edit: Bool determining whether to create new or edit existing
                address
            recurse: Bool determining whether to recurse into children (this
                is only functional when edit=True)
        Return:
            Recordset of partner address
        """
        address = self.search([('partner_id', '=', partner.id)], limit=1)
        vals = self.address_id._get_partner_sync_vals(partner)
        _logger.debug('_get_by_partner %s, %s, %s' % (address, partner, vals))
        if not edit:
            return address
        if not address:
            vals['partner_id'] = partner.id
            address = self.create(vals)
        else:
            address.write(vals)
        if recurse:
            for child in partner.child_ids:
                self._get_by_partner(child, edit, recurse)
        return address


@carepoint
class CarepointAddressAbstractImportMapper(CarepointImportMapper):

    @staticmethod
    def _has_empty_address(partner):
        """ It determines if the provided partner has an empty address.
        Currently only looks at ``street`` and ``street2``.
        """
        return not any([partner.street, partner.street2])

    def _get_partner_defaults(self, record):
        """ It provides a method for partner defaults
        This could be handy to provide custom defaults via modules
        Params:
            record: ``dict`` of carepoint record
        """
        return {
            'type': 'delivery',
            'customer': True,
        }

    def partner_id(self, record, medical_entity):
        """ It returns either the existing partner or a new one
        Params:
            record: ``dict`` of carepoint record
            medical_entity: Recordset with a ``partner_id`` column
        Return:
            ``dict`` of values for mapping
        """
        if CarepointAddressAbstractImportMapper._has_empty_address(
            medical_entity.commercial_partner_id
        ):
            _logger.info('Empty address, sending %s',
                         medical_entity.commercial_partner_id)
            partner = medical_entity.commercial_partner_id
        else:
            _logger.info('Full address, sending defaults')
            vals = self._get_partner_defaults(record)
            vals.update({
                'parent_id': medical_entity.commercial_partner_id.id,
            })
            partner = self.env['res.partner'].create(vals)
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
    @only_create
    def address_id(self, record):
        binder = self.binder_for('carepoint.carepoint.address')
        address_id = binder.to_odoo(record['addr_id'])
        return {'address_id': address_id}


@carepoint
class CarepointAddressAbstractImporter(CarepointImporter):
    _model_name = 'carepoint.address.abstract'

    def _import_dependencies(self):
        """ Import depends for record """
        self._import_dependency(self.carepoint_record['addr_id'],
                                'carepoint.carepoint.address')

    def _create(self, data):  # pragma: no cover
        binding = super(CarepointAddressAbstractImporter, self)._create(data)
        add_checkpoint(
            self.session, binding._name, binding.id, binding.backend_id.id
        )
        return binding


@carepoint
class CarepointAddressAbstractExportMapper(ExportMapper):

    @mapping
    def addr_id(self, binding):
        binder = self.binder_for('carepoint.carepoint.address')
        rec_id = binder.to_backend(binding.address_id.id)
        return {'addr_id': rec_id}

    @mapping
    def static_defaults(self, binding):
        return {
            'priority': 1,
            'addr_type_cn': 1,
            'app_flags': 0,
        }


@carepoint
class CarepointAddressAbstractExporter(CarepointExporter):
    _model_name = 'carepoint.address.abstract'

    def _export_dependencies(self):
        self._export_dependency(self.binding_record.address_id,
                                'carepoint.carepoint.address')
