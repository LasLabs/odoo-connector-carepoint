# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbAllergenRel(models.Model):
    _name = 'fdb.allergen.rel'
    _description = 'Fdb Allergen Rel'
    _inherits = {'fdb.allergen.group': 'group_id'}

    group_id = fields.Many2one(
        string='Group',
        comodel_name='fdb.allergen.group',
        index=True,
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer()
    hic_rel_no = fields.Integer()
