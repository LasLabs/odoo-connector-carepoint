# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbGcn(models.Model):
    _name = 'fdb.gcn'
    _description = 'Fdb Gcn'

    gcn = fields.Integer()
    update_yn = fields.Boolean()
