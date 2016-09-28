# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbAllergen(models.Model):
    _name = 'fdb.allergen'
    _description = 'Fdb Allergen'
    _inherits = {'fdb.allergen.rel': 'allergen_rel_id'}

    allergen_rel_id = fields.Many2one(
        string='Allergen Relation',
        comodel_name='fdb.allergen.rel',
        required=True,
        index=True,
        ondelete='restrict',
    )
    code = fields.Char(
        help='Hierarchical Ingredient Code',
    )
    name = fields.Char()
    hic_root = fields.Integer()
    potentially_inactive = fields.Boolean()
    state = fields.Integer()
