# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper, trim
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class CarepointFdbAllergenDesc(models.Model):
    _name = 'carepoint.fdb.allergen.desc'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.allergen.desc': 'odoo_id'}
    _description = 'Carepoint FdbAllergenDesc'
    _cp_lib = 'fdb_allergen_desc'

    odoo_id = fields.Many2one(
        string='FdbAllergenDesc',
        comodel_name='fdb.allergen.desc',
        required=True,
        ondelete='restrict'
    )


class FdbAllergenDesc(models.Model):
    _inherit = 'fdb.allergen.desc'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.allergen.desc',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbAllergenDescAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.allergen.desc'


@carepoint
class FdbAllergenDescBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbAllergenDesc.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = 'carepoint.fdb.allergen.desc'


@carepoint
class FdbAllergenDescImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.allergen.desc'
    direct = [
        ('hicl_seqno', 'carepoint_id'),
        (trim('gnn'), 'generic_name'),
        (trim('gnn60'), 'generic_description'),
    ]


@carepoint
class FdbAllergenDescImporter(CarepointImporter):
    _model_name = 'carepoint.fdb.allergen.desc'
    _base_mapper = FdbAllergenDescImportMapper
