# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbForm(models.Model):
    _name = 'fdb.form'
    _description = 'Fdb Form'
    _inherits = {'medical.drug.form': 'form_id'}

    form_id = fields.Many2one(
        string='Form',
        comodel_name='medical.drug.form',
        required=True,
        ondelete='cascade',
    )
    gcdf = fields.Char()
    update_yn = fields.Boolean()
