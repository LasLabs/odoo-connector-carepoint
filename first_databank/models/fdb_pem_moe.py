# -*'coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, _


TYPES = [
    ('A', _('Document Information')),
    ('B', _('Blank Line')),
    ('C', _('Common Brand Name')),
    ('D', _('Missed Dose')),
    ('F', _('Phonetic Pronunciation')),
    ('H', _('How to Use')),
    ('I', _('Drug Interaction')),
    ('M', _('Medical Alert')),
    ('N', _('Notes')),
    ('O', _('Overdose')),
    ('P', _('Precautions')),
    ('R', _('Storage')),
    ('S', _('Side Effects')),
    ('T', _('Monograph Title')),
    ('U', _('Uses')),
    ('V', _('Other Uses')),
    ('W', _('Warning')),
    ('Z', _('Disclaimer')),
]


class FdbPemMoe(models.Model):
    _name = 'fdb.pem.moe'
    _description = 'Fdb Pem Moe'
    _order = 'mogc_id ASC, pemono_sn ASC'

    mogc_ids = fields.Many2many(
        comodel_name='fdb.pem.mogc',
        required=True,
        index=True,
    )
    pemono_sn = fields.Integer(
        required=True,
        index=True,
    )
    pemtxtei = fields.Selection(
        TYPES,
        required=True,
    )
    pemtxte = fields.Char(required=True)
    pemgndr = fields.Char()
    pemage = fields.Char()
    update_yn = fields.Boolean()
