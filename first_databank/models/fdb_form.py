# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbForm(models.Model):
    _name = 'fdb.form'
    _description = 'Fdb Form'

    dose = fields.Char()
    gcdf_desc = fields.Char()
    update_yn = fields.Boolean()
