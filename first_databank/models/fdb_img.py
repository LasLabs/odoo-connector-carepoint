# -*- coding: utf-8 -*-
# © 2015-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class FdbImg(models.Model):
    _name = 'fdb.img'
    _inherits = {'ir.attachment': 'attachment_id'}
    _description = 'Fdb Img'
    attachment_id = fields.Many2one(
        string='Attachment',
        comodel_name='ir.attachment',
        required=True,
        ondelete='cascade',
    )
    image_date_ids = fields.One2many(
        string='Image Dates',
        comodel_name='fdb.img.date',
        inverse_name='image_id',
    )
