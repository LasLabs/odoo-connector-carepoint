# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields, api
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import CarepointImporter

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
        compute='_compute_partner_id',
        inverse='_set_partner_id',
    )

    @api.multi
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

    def _create(self, data):
        binding = super(CarepointAddressAbstractImporter, self)._create(data)
        add_checkpoint(
            self.session, binding._name, binding.id, binding.backend_id.id
        )
        return binding
