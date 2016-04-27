# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbGcn(models.Model):
    _name = 'fdb.gcn'
    _description = 'Fdb Gcn'
    _inherits = {'medical.medicament.gcn': 'gcn_id'}

    gcn_id = fields.Many2one(
        string='GCN',
        comodel_name='medical.medicament.gcn',
        ondelete='cascade',
        required=True,
    )
    update_yn = fields.Boolean()
