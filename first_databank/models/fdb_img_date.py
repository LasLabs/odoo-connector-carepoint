# -*- coding: utf-8 -*-
# © 2015-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbImgDate(models.Model):
    _name = 'fdb.img.date'
    _description = 'Fdb Img Date'
    start_date = fields.Datetime()
    stop_date = fields.Datetime()
    img_id = fields.Integer()
