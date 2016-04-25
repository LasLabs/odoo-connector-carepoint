# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields
from openerp.addons.connector.connector import ConnectorEnvironment
from openerp.addons.connector.checkpoint import checkpoint


def get_environment(session, model_name, backend_id):
    """ Create an environment to work with.  """
    backend_record = session.env['carepoint.backend'].browse(backend_id)
    env = ConnectorEnvironment(backend_record, session, model_name)
    lang = backend_record.default_lang_id
    lang_code = lang.code if lang else 'en_US'
    if lang_code == session.context.get('lang'):
        return env
    else:
        with env.session.change_context(lang=lang_code):
            return env


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
        ondelete='restrict',
    )
    # fields.Char because 0 is a valid Carepoint ID
    carepoint_id = fields.Char(string='ID on Carepoint')

    _sql_constraints = [
        ('carepoint_uniq', 'unique(backend_id, carepoint_id)',
         'A binding already exists with the same Carepoint ID.'),
    ]


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
