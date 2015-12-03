# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Dave Lasley <dave@laslabs.com>
#    Copyright: 2015 LasLabs, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import openerp
from openerp.addons.connector.connector import Binder
from ..backend import magento


class CarepointBinder(Binder):
    """ Generic Binder for Carepoint """


@carepoint
class CarepointModelBinder(CarepointBinder):
    """
    Bindings are done directly on the binding model.
    Binding models are models called ``carepoint.{normal_model}``,
    like ``carepoint.res.partner`` or ``carepoint.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Carepoint ID, the ID of the Carepoint Backend and the additional
    fields belonging to the Carepoint instance.
    """
    _model_name = [
        'carepoint.store',
    ]

    def to_odoo(self, external_id, unwrap=False, browse=False):
        """ Give the Odoo ID for an external ID
        :param external_id: external ID for which we want the Odoo ID
        :param unwrap: if True, returns the normal record (the one
                       inherits'ed), else return the binding record
        :param browse: if True, returns a recordset
        :return: a recordset of one record, depending on the value of unwrap,
                 or an empty recordset if no binding is found
        :rtype: recordset
        """
        bindings = self.model.with_context(active_test=False).search(
            [('carepoint_id', '=', str(external_id)),
             ('backend_id', '=', self.backend_record.id)]
        )
        if not bindings:
            return self.model.browse() if browse else None
        assert len(bindings) == 1, "Several records found: %s" % (bindings,)
        if unwrap:
            return bindings.odoo_id if browse else bindings.odoo_id.id
        else:
            return bindings if browse else bindings.id

    def to_backend(self, record_id, wrap=False):
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
            binding = self.model.with_context(active_test=False).search(
                [('odoo_id', '=', record_id),
                 ('backend_id', '=', self.backend_record.id),
                 ]
            )
            if binding:
                binding.ensure_one()
                return binding.carepoint_id
            else:
                return None
        if not record:
            record = self.model.browse(record_id)
        assert record
        return record.carepoint_id

    def bind(self, external_id, binding_id):
        """ Create the link between an external ID and an Odoo ID and
        update the last synchronization date.
        :param external_id: External ID to bind
        :param binding_id: Odoo ID to bind
        :type binding_id: int
        """
        # the external ID can be 0 on Carepoint! Prevent False values
        # like False, None, or "", but not 0.
        assert (external_id or external_id == 0) and binding_id, (
            "external_id or binding_id missing, "
            "got: %s, %s" % (external_id, binding_id)
        )
        # avoid to trigger the export when we modify the `carepoint_id`
        now_fmt = odoo.fields.Datetime.now()
        if not isinstance(binding_id, odoo.models.BaseModel):
            binding_id = self.model.browse(binding_id)
        binding_id.with_context(connector_no_export=True).write(
            {'carepoint_id': str(external_id),
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
