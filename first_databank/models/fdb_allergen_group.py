# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbAllergenGroup(models.Model):
    _name = 'fdb.allergen.group'
    _description = 'Fdb Allergen Group'

    code = fields.Char(
        help='DAM Specific Allergen Group Code',
    )
    name = fields.Char()
    potentially_inactive = fields.Boolean()
    state = fields.Integer()
