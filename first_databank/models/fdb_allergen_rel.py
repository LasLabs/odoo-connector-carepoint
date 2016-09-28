# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbAllergenRel(models.Model):
    _name = 'fdb.allergen.rel'
    _description = 'Fdb Allergen Rel'

    code = fields.Char(
        help='Hierarchical Ingredient Code',
    )
    name = fields.Char()
    hic_root = fields.Integer()
    potentially_inactive = fields.Boolean()
    state = fields.Integer()
