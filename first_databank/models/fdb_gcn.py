# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


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
    monograph_ids = fields.Many2many(
        string='Monographs',
        comodel_name='fdb.pem.mogc',
        compute='_compute_monograph_ids',
    )
    update_yn = fields.Boolean()

    @api.multi
    def _compute_monograph_ids(self):
        for record in self:
            monographs = self.env['fdb.pem.mogc'].search([
                ('gcn_ids', '=', record.gcn_id.id),
            ])
            record.monograph_ids = [(6, 0, monographs.ids)]
