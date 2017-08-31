# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import odoo

from odoo.addons.connector_v9.connector import Binder

from ..backend import carepoint


_logger = logging.getLogger(__name__)


class CarepointBinder(Binder):
    """ Generic Binder for Carepoint """


@carepoint
class CarepointModelBinder(CarepointBinder):
    """ Bindings are done directly on the binding model.
    Binding models are models called ``carepoint.{normal_model}``,
    like ``carepoint.res.partner`` or ``carepoint.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Carepoint ID, the ID of the Carepoint Backend and the additional
    fields belonging to the Carepoint instance.
    """
    _model_name = [
        'carepoint.carepoint.store',
        'carepoint.org.bind',
        'carepoint.carepoint.item',
        'carepoint.medical.physician',
        'carepoint.medical.patient',
        'carepoint.medical.pathology',
        'carepoint.medical.pathology.code.type',
        'carepoint.medical.patient.disease',
        'carepoint.medical.prescription.order',
        'carepoint.medical.prescription.order.line',
        'carepoint.carepoint.phone',
        'carepoint.carepoint.phone.patient',
        'carepoint.carepoint.phone.physician',
        'carepoint.carepoint.phone.organization',
        'carepoint.carepoint.phone.store',
        'carepoint.rx.ord.ln',
        'carepoint.carepoint.address',
        'carepoint.carepoint.address.patient',
        'carepoint.carepoint.address.physician',
        'carepoint.carepoint.address.organization',
        'carepoint.carepoint.address.store',
        'carepoint.carepoint.account',
        'carepoint.carepoint.vendor',
        'carepoint.account.invoice.line',
        'carepoint.sale.order',
        'carepoint.sale.order.line',
        'carepoint.procurement.order',
        'carepoint.stock.picking',
        'carepoint.stock.warehouse',
        'carepoint.res.users',
        'carepoint.fdb.ndc',
        'carepoint.fdb.gcn',
        'carepoint.fdb.gcn.seq',
        'carepoint.fdb.lbl.rid',
        'carepoint.fdb.route',
        'carepoint.fdb.form',
        'carepoint.fdb.img',
        'carepoint.fdb.img.id',
        'carepoint.fdb.img.date',
        'carepoint.fdb.img.mfg',
        'carepoint.fdb.imglbl.rid',
        'carepoint.fdb.unit',
        'carepoint.fdb.ndc.cs.ext',
        'carepoint.fdb.pem.mogc',
        'carepoint.fdb.pem.moe',
    ]

    def to_odoo(self, external_id, unwrap=True, browse=False):
        """ Give the Odoo ID for an external ID
        :param external_id: external ID for which we want the Odoo ID
        :param unwrap: if True, returns the normal record (the one
                       inherits'ed), else return the binding record
        :param browse: if True, returns a recordset
        :return: a recordset of one record, depending on the value of unwrap,
                 or an empty recordset if no binding is found
        :rtype: recordset
        """
        bindings = self.model.with_context(active_test=False).search([
            ('carepoint_id', '=', str(external_id)),
            ('backend_id', '=', self.backend_record.id)
        ])
        if not bindings:
            return self.model.browse() if browse else None
        assert len(bindings) == 1, odoo._(
            "Several records found: %s"
        ) % (bindings)
        if unwrap:
            return bindings.odoo_id if browse else bindings.odoo_id.id
        else:
            return bindings if browse else bindings.id

    def to_backend(self, record_id, wrap=True):
        """ Give the external ID for an Odoo ID
        :param record_id: Odoo ID for which we want the external id
                          or a recordset with one record
        :param wrap: if False, record_id is the ID of the binding,
            if True, record_id is the ID of the normal record, the
            method will search the corresponding binding and returns
            the backend id of the binding
        :return: backend identifier of the record
        """
        record = self.model.browse()
        if isinstance(record_id, odoo.models.BaseModel):
            record_id.ensure_one()
            record = record_id
            record_id = record_id.id
        if wrap:
            binding = self.model.with_context(active_test=False).search([
                ('odoo_id', '=', record_id),
                ('backend_id', '=', self.backend_record.id),
            ])
            if binding:
                binding.ensure_one()
                return binding.carepoint_id
            else:
                return None
        if not record:
            record = self.model.browse(record_id)
        assert record
        return record.id

    def bind(self, external_id, binding_id):
        """ Create the link between an external ID and an Odoo ID and
        update the last synchronization date.
        :param external_id: External ID to bind
        :param binding_id: Odoo ID to bind
        :type binding_id: int
        """
        # the external ID can be 0 on Carepoint! Prevent False values
        # like False, None, or "", but not 0.
        assert (external_id or external_id is 0) and binding_id, (
            "external_id or binding_id missing, "
            "got: %s, %s" % (external_id, binding_id)
        )
        # avoid to trigger the export when we modify the `carepoint_id`
        now_fmt = odoo.fields.Datetime.now()
        if not isinstance(binding_id, odoo.models.BaseModel):
            binding_id = self.model.browse(binding_id)
        binding_id.with_context(connector_no_export=True).write({
            'carepoint_id': str(external_id),
            'sync_date': now_fmt,
        })

    def unwrap_binding(self, binding_id, browse=False):
        """ For a binding record, gives the normal record.
        Example: when called with a ``carepoint.product.product`` id,
        it will return the corresponding ``product.product`` id.
        :param browse: when True, returns a browse_record instance
                       rather than an ID
        """
        if isinstance(binding_id, odoo.models.BaseModel):
            binding = binding_id
        else:
            binding = self.model.browse(binding_id)
        odoo_record = binding.odoo_id
        if browse:
            return odoo_record
        return odoo_record.id

    def unwrap_model(self):
        """ For a binding model, gives the name of the normal model.
        Example: when called on a binder for ``carepoint.product.product``,
        it will return ``product.product``.
        This binder assumes that the normal model lays in ``odoo_id`` since
        this is the field we use in the ``_inherits`` bindings.
        """
        try:
            column = self.model._fields['odoo_id']
        except KeyError:
            raise ValueError('Cannot unwrap model %s, because it has '
                             'no odoo_id field' % self.model._name)
        return column.comodel_name

    def create_bind(self, record):
        """ It creates a new binding for the input, non-bound record

        It also attempts to identify polymorphic inherits, assigning those
        record IDs as part of the create values in order to circumvent auto
        record creation via the delegation mechanism.

        :param record: Singleton of non-bound record
        :param backend: Singleton of backend record. False for default
        :return: Singleton of binding record
        """
        _logger.debug('In create_bind w/ %s and %s', self.model, record)
        binding_record = self.model.search([
            ('odoo_id', '=', record.id),
            ('backend_id', '=', self.backend_record.id),
        ])
        if binding_record:
            binding_record.assert_one()
            return binding_record
        vals = {
            'odoo_id': record.id,
            'backend_id': self.backend_record.id,
        }
        _logger.debug('Creating bind record with %s', vals)
        return self.model.create(vals)
