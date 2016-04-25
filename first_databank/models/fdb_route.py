# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbRoute(models.Model):
    _name = 'fdb.route'
    _description = 'Fdb Route'

    rt = fields.Char()
    gcrt2 = fields.Char()
    gcrt_desc = fields.Char()
    systemic = fields.Char()
    update_yn = fields.Boolean()
