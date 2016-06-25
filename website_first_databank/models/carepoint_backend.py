# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class CarepointBackend(models.Model):
    _inherit = 'carepoint.backend'

    manage_product_description = fields.Boolean(
        default=True,
        help='Check this to automatically update imported product '
             'descriptions using FDB Monograph data.',
    )
    website_product_template_id = fields.Many2one(
        string='Website Product Template',
        comodel_name='ir.ui.view',
        default=lambda s: s.env.ref(
            'website_first_databank.website_medicament_description'
        ).id,
        required=True,
    )
