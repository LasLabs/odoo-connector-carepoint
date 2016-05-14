# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbGcnSeq(models.Model):
    _name = 'fdb.gcn.seq'
    _description = 'Fdb Gcn Seq'

    gcn_seqno = fields.Integer()
    hic3 = fields.Char()
    hicl_seqno = fields.Integer()
    str = fields.Char()
    gtc = fields.Integer()
    tc = fields.Integer()
    dcc = fields.Char()
    gcnseq_gi = fields.Integer()
    gender = fields.Char()
    hic3_seqn = fields.Integer()
    str60 = fields.Char()
    update_yn = fields.Boolean()
    form_id = fields.Many2one(
        string='Form',
        comodel_name='fdb.form',
    )
    route_id = fields.Many2one(
        string='Route',
        comodel_name='fdb.route',
    )
