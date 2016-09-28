# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbAllergen(models.Model):
    _name = 'fdb.allergen'
    _description = 'Fdb Allergen'
    _inherits = {'fdb.allergen.rel': 'ingredient_id',
                 'fdb.allergen.desc': 'generic_id',
                 }

    code = fields.Char(
        help='Hierarchical Ingredient Code',
    )
    generic_id = fields.Many2one(
        string='Generic',
        comodel_name='fdb.allergen.desc',
        ondelete='restrict',
    )
    ingredient_id = fields.Many2one(
        string='Ingredient',
        comodel_name='fdb.allergen.rel',
        ondelete='restrict',
    )
    hic_rel_no = fields.Integer()
