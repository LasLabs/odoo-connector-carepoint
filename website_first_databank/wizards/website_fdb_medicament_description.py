# -*- coding: utf-8 -*-
# © 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields

from odoo.addons.first_databank.models.fdb_pem_moe import TYPES


class WebsiteFdbMedicamentDescription(models.TransientModel):
    _name = 'website.fdb.medicament.description'
    _description = 'Website Fdb Medicament Description'

    medicament_ids = fields.Many2many(
        string='Medicament',
        comodel_name='medical.medicament',
        default=lambda s: s._default_medicament_ids(),
        readonly=True,
    )
    gcn_id = fields.Many2one(
        string='GCN',
        comodel_name='medical.medicament.gcn',
        compute='_compute_gcn_id',
        readonly=True,
    )
    monograph_id = fields.Many2one(
        string='Monograph',
        comodel_name='fdb.pem.mogc',
        default=lambda s: s._default_monograph_id(),
        domain="[('gcn_id', '=', gcn_id)]",
    )
    template_id = fields.Many2one(
        string='Template',
        comodel_name='ir.ui.view',
        default=lambda s: s._default_template_id(),
    )
    monograph_html = fields.Html()

    @api.model
    def _default_medicament_ids(self):
        model = 'medical.medicament'
        if self.env.context.get('active_model') != model:
            return
        return [(6, 0, self.env.context.get('active_ids', []))]

    @api.multi
    @api.depends('medicament_ids.gcn_id')
    def _compute_gcn_id(self):
        for record in self:
            if record.medicament_ids:
                record.gcn_id = record.medicament_ids[0].gcn_id

    @api.model
    def _default_monograph_id(self):
        medicament_ids = self.env['medical.medicament'].browse(
            self._default_medicament_ids()[0][2]
        )
        fdb_gcn_id = self.env['fdb.gcn'].search([
            ('gcn_id', '=', medicament_ids[0].gcn_id.id),
        ],
            limit=1,
        )
        if not fdb_gcn_id.monograph_ids:
            return
        return fdb_gcn_id.monograph_ids[0].id

    @api.model
    def _default_template_id(self):
        template_id = self.env.ref(
            'website_first_databank.website_medicament_description',
        )
        if template_id:
            return template_id.id

    @api.multi
    @api.onchange('template_id')
    def _onchange_template_id(self):
        self._render_save()

    @api.multi
    def sync_description(self):
        """ Sync the product website description from FDB """
        for record in self:
            html = record.monograph_html
            for medicament_id in record.medicament_ids:
                medicament_id.product_id.website_description = html

    @api.multi
    def _render_save(self):
        for record in self:
            record.monograph_html = record._render()

    @api.multi
    def _render(self):
        """ Override this in order to customize the template. """
        template_vals = self._get_template_values()
        if not template_vals:
            return
        return self.template_id.render(
            template_vals,
            engine='ir.qweb',
        )

    @api.multi
    def _get_template_values(self):
        """ Return values to inject in Monograph template
        Use this method to add additional attributes via child classes
        """
        self.ensure_one()
        if not all((self.medicament_ids, self.monograph_id)):
            return
        return {
            'medicament': self.medicament_ids[0],
            'monograph': self.monograph_id,
            'sections': self.monograph_id._get_sections_dict(),
            'section_headers': dict((k, v) for k, v in TYPES),
        }
