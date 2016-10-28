# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class FdbRoute(models.Model):
    _name = 'fdb.route'
    _description = 'Fdb Route'
    _inherits = {'medical.drug.route': 'route_id'}

    route_id = fields.Many2one(
        string='Route',
        comodel_name='medical.drug.route',
        required=True,
        ondelete='cascade',
    )
    rt = fields.Char()
    systemic = fields.Char()
    update_yn = fields.Boolean()
