# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.connector.connector import Binder
from .unit.export_synchronizer import export_record
# from .unit.delete_synchronizer import export_delete_record
from .connector import get_environment
from odoo.addons.connector.event import (on_record_write,
                                         on_record_create,
                                         # on_record_unlink
                                         )


import logging
_logger = logging.getLogger(__name__)


# @on_record_create(model_names=['carepoint.medical.patient',
#                                'carepoint.carepoint.address',
#                                'carepoint.carepoint.address.patient',
#                                ])
def delay_export(session, model_name, record_id, vals):
    """ Delay a job which export a binding record.
    (A binding record being a ``carepoint.res.partner``,
    ``carepoint.product.product``, ...)
    """
    if session.context.get('connector_no_export'):
        return
    fields = vals.keys()
    export_record.delay(session, model_name, record_id, fields=fields)


@on_record_write(model_names=['medical.prescription.order.line',
                              'medical.patient',
                              'carepoint.address',
                              'carepoint.phone',
                              'carepoint.address.patient',
                              'carepoint.phone.patient',
                              'carepoint.organization',
                              'carepoint.address.organization',
                              'carepoint.phone.organization',
                              'medical.physician',
                              'carepoint.address.physician',
                              'carepoint.phone.physician',
                              'sale.order',
                              'sale.order.line',
                              'procurement.order',
                              ])
def delay_export_all_bindings(session, model_name, record_id, vals):
    """ Delay a job which export all the bindings of a record.
    In this case, it is called on records of normal models and will delay
    the export for all the bindings.
    """
    if session.context.get('connector_no_export'):
        return
    record = session.env[model_name].browse(record_id)
    fields = vals.keys()
    for binding in record.carepoint_bind_ids:
        export_record.delay(session, binding._name, binding.id,
                            fields=fields)


@on_record_create(model_names=['medical.prescription.order.line',
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
                               ])
def delay_create(session, model_name, record_id, vals):
    """ Create a new binding record, then trigger delayed export
    In this case, it is called on records of normal models to create
    binding record, and trigger external system export
    """
    if session.context.get('connector_no_export'):
        return
    bind_model_name = session.env[model_name].carepoint_bind_ids._name
    record = session.env[model_name].browse(record_id)
    env = get_environment(session, bind_model_name)
    binder = env.get_connector_unit(Binder)
    bind_record = binder.create_bind(record)
    delay_export(session, bind_model_name, bind_record.id, vals)


# @on_record_unlink(model_names=['carepoint.medical.patient',
#                                'carepoint.carepoint.address',
#                                'carepoint.carepoint.address.patient',
#                                ])
# def delay_unlink(session, model_name, record_id):
#     """ Delay a job which delete a record on Carepoint.
#     Called on binding records."""
#     record = session.env[model_name].browse(record_id)
#     env = get_environment(session, model_name, record.backend_id.id)
#     binder = env.get_connector_unit(Binder)
#     carepoint_id = binder.to_backend(record_id, wrap=False)
#     if carepoint_id:
#         export_delete_record.delay(session, model_name,
#                                    record.backend_id.id, carepoint_id)


@on_record_write(model_names=['carepoint.phone'])
def sync_phone_to_partner(session, model_name, record_id, vals):
    """ Triggers phone sync to partner when written """
    session.env[model_name].browse(record_id)._sync_partner()
