# -*- coding: utf-8 -*-
# © 2015-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbImgId(models.Model):
    _name = 'fdb.img.id'
    df_id = fields.Integer(
        help='This is an unidentified relation',
    )
    ndc_id = fields.Many2one(
        string='FDB NDC',
        comodel_name='fdb.ndc',
    )
    manufacturer_id = fields.Many2one(
        string='Image Manufacturer',
        comodel_name='fdb.img.mfg',
    )
    image_ids = fields.One2many(
        string='Images',
        comodel_name='fdb.img.date',
        inverse_name='relation_id',
    )
