# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import OrderedDict
import re

from openerp import models, fields, api


class FdbPemMogc(models.Model):
    _name = 'fdb.pem.mogc'
    _description = 'Fdb Pem Mogc'

    gcn_id = fields.Many2one(
        string='GCN',
        comodel_name='fdb.gcn',
        ondelete='cascade',
        required=True,
        index=True,
    )
    pemono = fields.Integer(
        index=True,
        required=True,
    )
    moe_ids = fields.One2many(
        string='Monograph Data',
        comodel_name='fdb.pem.moe',
        inverse_name='mogc_id',
    )
    monograph = fields.Text(
        compute='_compute_monograph',
        store=True,
    )
    update_yn = fields.Boolean()

    @api.multi
    @api.depends('moe_ids')
    def _compute_monograph(self):
        """ Loop monograph pieces and create string
        Assumes that monograph piece ordering is by ``pemono_sn ASC`` as is
        default
        """
        for rec_id in self:
            rec_id.monograph = self._get_sections()

    @api.multi
    def _get_sections(self, sections=None, remove_headers=True):
        """ Return monograph sections as string

        Params:
            sections: List of section references to filter by
            remove_headers: Some monographs include their headers, remove?
        Returns:
            Joined monograph string
        """
        monograph = []
        for val in self._get_sections_dict(sections).values():
            monograph.extend([val, '\r'])
        return ' '.join(monograph)

    @api.multi
    def _get_sections_dict(self, sections=None, remove_headers=True):
        """ Return monograph as an OrderedDict of joined strings

        Params:
            sections: List of section references to filter by
            remove_headers: Some monographs include their headers, remove?
        Returns:
            OrderedDict of joined section strings
        """
        self.ensure_one()
        monograph = OrderedDict()
        moe_ids = self.moe_ids
        header_re = re.compile(r'^[A-Z \(\)]+: ')
        if sections is not None:
            moe_ids = moe_ids.filtered(
                lambda r: r.pemtxtei in sections
            )
        for moe_id in moe_ids:
            if moe_id.pemtxtei != 'B':
                text = moe_id.pemtxte.strip()
                if remove_headers:
                    text = header_re.sub('', text, 1)
                try:
                    monograph[moe_id.pemtxtei].append(text)
                except KeyError:
                    monograph[moe_id.pemtxtei] = [text]
        for key, val in monograph.iteritems():
            monograph[key] = ' '.join(val)
        return monograph
