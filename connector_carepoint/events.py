# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.connector.connector import Binder
from odoo.addons.component.core import Component


class CarepointEventListenerBase(Component):

    _name = 'carepoint.event.listener.base'
    _inherit ='base.event.listener'
    _collection = 'carepoint.backend'

    def create_bind(self, record, backend=None):
        """ It creates a new binding for the input, non-bound record

        It also attempts to identify polymorphic inherits, assigning those
        record IDs as part of the create values in order to circumvent auto
        record creation via the delegation mechanism.

        :param record: Singleton of non-bound record
        :param backend: Singleton of backend record. False for default
        :return: Singleton of binding record
        """
        if not backend:
            backend = self.env['carepoint.binding'].get_default(
                record.get('company_id'),
            )
        Model = self.env[record.carepoint_bind_ids._name]
        binding_record = Model.search([
            ('odoo_id', '=', record.id),
            ('backend_id', '=', backend.id),
        ])
        if binding_record:
            binding_record.assert_one()
            return binding_record
        vals = {
            'odoo_id': record.id,
            'backend_id': backend.id,
        }
        return Model.create(vals)


class CarepointEventListenerCreate(CarepointEventListenerBase):

    _name = 'carepoint.event.listener.create'
    _apply_on = [
       'medical.prescription.order.line',
       'medical.patient',
       'carepoint.address',
       'carepoint.phone',
       'carepoint.address.patient',
       'carepoint.phone.patient',
       'carepoint.organization',
       'carepoint.address.organization',
       'carepoint.phone.organization',
       'carepoint.account',
       'medical.physician',
       'carepoint.address.physician',
       'carepoint.phone.physician',
       'sale.order',
       'sale.order.line',
       'procurement.order',
    ]

    def on_record_create(self, record, fields=None):
        binding = self.create_bind(record)
        binding.with_delay().export_record(fields)


class CarepointEventListenerWrite(CarepointEventListenerBase):

    _name = 'carepoint.event.listener.write'
    _apply_on = CarepointEventListenerCreate._apply_on + [
        'res.users',
    ]

    def on_record_write(self, record, fields=None):
        record.with_delay().export_record(fields)
