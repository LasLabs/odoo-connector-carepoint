# -*- coding: utf-8 -*-
# © 2015-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbImgMfg(models.Model):
    _name = 'fdb.img.mfg'
    _description = 'Fdb Img Mfg'
    mfg_name = fields.Char()
