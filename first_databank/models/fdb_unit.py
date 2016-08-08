# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbUnit(models.Model):
    _name = 'fdb.unit'
    _description = 'Fdb Gcn'
    _inherits = {'product.uom': 'uom_id'}

    uom_id = fields.Many2one(
        string='Unit of Measure',
        comodel_name='product.uom',
        ondelete='cascade',
        required=True,
    )
    str30 = fields.Char()
    str60 = fields.Char()
    update_yn = fields.Boolean()
