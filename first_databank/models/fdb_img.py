# -*- coding: utf-8 -*-
# © 2015-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbImg(models.Model):
    _name = 'fdb.img'
    _description = 'Fdb Img'
    file_name = fields.Char()
    data = fields.Binary(
        attachment=True,
    )
