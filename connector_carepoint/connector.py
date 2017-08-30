# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api

from odoo.addons.queue_job.job import job, related_action

from odoo.addons.connector.connector import ConnectorEnvironment
from odoo.addons.connector.checkpoint import checkpoint

from .related_action import unwrap_binding
from .unit.import_synchronizer import CarepointImporter, DelayedBatchImporter
from .unit.export_synchronizer import CarepointExporter



def get_environment(session, model_name, backend=None):
    """ Create an environment to work with.  """
    if not backend:
        backend = session.env[model_name]._default_backend()
    elif isinstance(backend, int):
        backend = session.env['carepoint.backend'].browse(backend)
    env = ConnectorEnvironment(backend, session, model_name)
    return env
    # @TODO: Multiple lang support. Seems not needed.
    # lang = backend_record.default_lang_id
    # lang_code = lang.code if lang else 'en_US'
    # if lang_code == session.context.get('lang'):
    #     return env
    # else:
    #     with env.session.change_context(lang=lang_code):
    #         return env


class CarepointBinding(models.AbstractModel):
    """ Abstract Model for the Bindigs.
    All the models used as bindings between Carepoint and Odoo
    (``carepoint.res.partner``, ``carepoint.product.product``, ...) should
    ``_inherit`` it.
    """
    _name = 'carepoint.binding'
    _inherit = 'external.binding'
    _description = 'Carepoint Binding (abstract)'

    # odoo_id = odoo-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='carepoint.backend',
        string='Carepoint Backend',
        required=True,
        readonly=True,
        ondelete='restrict',
        default=lambda s: s._default_backend(),
    )
    # fields.Char because 0 is a valid Carepoint ID
    carepoint_id = fields.Char(string='ID on Carepoint')
    created_at = fields.Date('Created At (on Carepoint)')
    updated_at = fields.Date('Updated At (on Carepoint)')

    _sql_constraints = [
        ('carepoint_uniq', 'unique(backend_id, carepoint_id)',
         'A binding already exists with the same Carepoint ID.'),
    ]

    @api.model
    def _default_backend(self, company=None):
        if company is None:
            company = self.env.user.company_id
        return self.env['carepoint.backend'].search([
            ('is_default', '=', True),
            ('active', '=', True),
            ('company_id', '=', company.id),
        ])

    @api.model
    @job(default_channel='root.carepoint')
    def import_record(self, backend, carepoint_id, force=False):
        """ Import a record from Carepoint """
        backend.ensure_one()
        env = get_environment(session, self._name, backend)
        importer = env.get_connector_unit(CarepointImporter)
        _logger.debug('Importing CP Record %s from %s', carepoint_id, self._name)
        importer.run(carepoint_id, force=force)

    @api.model
    @job(default_channel='root.carepoint')
    def import_batch(self, backend, filters=None):
        """ Prepare a batch import of records from Carepoint """
        backend.ensure_one()
        env = get_environment(session, self._name, backend)
        importer = env.get_connector_unit(DelayedBatchImporter)
        importer.run(filters=filters)

    @api.multi
    @job(default_channel='root.carepoint')
    @related_action(action=unwrap_binding)
    def export_record(self, fields=None):
        """ Export a record to Carepoint """
        if self.context.get('connector_no_export'):
            return
        self.ensure_one()
        env = get_environment(self, self._name, self.backend_id)
        exporter = env.get_connector_unit(CarepointExporter)
        return exporter.run(binding_id, fields=fields)



def add_checkpoint(session, model_name, record_id, backend_id):
    """ Add a row in the model ``connector.checkpoint`` for a record,
    meaning it has to be reviewed by a user.
    :param session: current session
    :type session: :class:`odoo.addons.connector.session.ConnectorSession`
    :param model_name: name of the model of the record to be reviewed
    :type model_name: str
    :param record_id: ID of the record to be reviewed
    :type record_id: int
    :param backend_id: ID of the Carepoint Backend
    :type backend_id: int
    """
    return checkpoint.add_checkpoint(session, model_name, record_id,
                                     'carepoint.backend', backend_id)
