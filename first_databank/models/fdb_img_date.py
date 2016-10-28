# -*- coding: utf-8 -*-
# © 2015-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import models, fields, api


class FdbImgDate(models.Model):
    _name = 'fdb.img.date'
    _description = 'Fdb Img Date'
    _inherits = {'fdb.img': 'image_id'}

    start_date = fields.Datetime(
        required=True,
    )
    stop_date = fields.Datetime()
    image_id = fields.Many2one(
        string='Image',
        comodel_name='fdb.img',
        required=True,
        ondelete='restrict',
    )
    active = fields.Boolean(
        compute='_compute_active',
    )
    relation_id = fields.Many2one(
        string='Relation',
        comodel_name='fdb.img.id',
        inverse_name='relation_id',
    )

    @api.multi
    def _compute_active(self):
        """ It sets active to false if stop_date < today """
        for rec_id in self:
            if not rec_id.stop_date:
                pass
            stop_date = fields.Datetime.from_string(rec_id.stop_date)
            if stop_date < datetime.now():
                rec_id.active = False
