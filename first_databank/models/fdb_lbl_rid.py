# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class FdbLblRid(models.Model):
    _name = 'fdb.lbl.rid'
    _description = 'Fdb Lbl Rid'

    mfg = fields.Char()
    update_yn = fields.Boolean()
