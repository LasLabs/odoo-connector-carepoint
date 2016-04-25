# -*- coding: utf-8 -*-
# © 2015-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbImgId(models.Model):
    _name = 'fdb.img.id'
    df_id = fields.Integer()
    ndc = fields.Char()
    mfg_id = fields.Integer()
