# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbAllergenDesc(models.Model):
    _name = 'fdb.allergen.desc'
    _description = 'Fdb Allergen Desc'

    generic_name = fields.Char()
    generic_description = fields.Char()
