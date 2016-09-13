# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# from openerp.addons.connector.connector import Binder
from .unit.export_synchronizer import export_record
# from .unit.delete_synchronizer import export_delete_record
# from .connector import get_environment
from openerp.addons.connector.event import (on_record_write,
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


@on_record_write(model_names=['medical.patient',
                              'carepoint.address',
                              'carepoint.address.patient',
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
        export_record.delay(session, binding._model._name, binding.id,
                            fields=fields)


@on_record_create(model_names=['medical.patient',
                               'carepoint.address',
                               'carepoint.address.patient',
                               ])
def delay_create(session, model_name, record_id, vals):
    """ Create a new binding record, then trigger delayed export
    In this case, it is called on records of normal models to create
    binding record, and trigger external system export
    """
    model_obj = session.env['carepoint.%s' % model_name].with_context(
        connector_no_export=True,
    )
    if not len(model_obj.search([('odoo_id', '=', record_id)])):
        model_obj.create({
            'odoo_id': record_id,
        })
    delay_export_all_bindings(session, model_name, record_id, vals)


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
