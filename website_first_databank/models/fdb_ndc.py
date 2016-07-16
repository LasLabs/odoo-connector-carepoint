# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.connector_carepoint.backend import carepoint
from openerp.addons.connector_carepoint.models.fdb_ndc import (
    FdbNdcImporter
)


@carepoint(replacing=FdbNdcImporter)
class WebsiteFdbNdcImporter(FdbNdcImporter):

    def _after_import(self, binding):
        super(FdbNdcImporter, self)._after_import(binding)
        if binding.backend_id.manage_product_description:
            wizard_obj = self.env['website.fdb.medicament.description']
            fdb_gcn_id = self.env['fdb.gcn'].search([
                ('gcn_id', '=', binding.medicament_id.gcn_id.id),
            ],
                limit=1,
            )
            if not fdb_gcn_id.monograph_ids:
                return
            wizard_id = wizard_obj.create({
                'medicament_id': binding.medicament_id.id,
                'template_id':
                    binding.backend_id.website_product_template_id.id,
                'monograph_id': fdb_gcn_id.monograph_ids[0].id,
            })
            wizard_id._render_save()
            wizard_id.sync_description()
