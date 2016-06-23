# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbGcn(models.Model):
    _name = 'fdb.gcn'
    _description = 'Fdb Gcn'
    _inherits = {'medical.medicament.gcn': 'gcn_id',
                 'fdb.gcn.seq': 'gcn_seq_id',
                 }

    gcn_id = fields.Many2one(
        string='GCN',
        comodel_name='medical.medicament.gcn',
        ondelete='cascade',
        required=True,
    )
    gcn_seq_id = fields.Many2one(
        string='GCN Seq',
        comodel_name='fdb.gcn.seq',
        ondelete='cascade',
        required=True,
    )
    monograph_ids = fields.One2many(
        string='Monographs',
        comodel_name='fdb.pem.mogc',
        inverse_name='gcn_id',
    )
    update_yn = fields.Boolean()
