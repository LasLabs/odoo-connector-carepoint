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


class CarepointFdbAllergenRel(models.Model):
    _name = 'carepoint.fdb.allergen.rel'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.allergen.rel': 'odoo_id'}
    _description = 'Carepoint FdbAllergenRel'
    _cp_lib = 'fdb_allergen_rel'

    odoo_id = fields.Many2one(
        string='FdbAllergenRel',
        comodel_name='fdb.allergen.rel',
        required=True,
        ondelete='restrict'
    )


class FdbAllergenRel(models.Model):
    _inherit = 'fdb.allergen.rel'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.allergen.rel',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbAllergenRelAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.allergen.rel'


@carepoint
class FdbAllergenRelBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbAllergenRels.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = 'carepoint.fdb.allergen.rel'


@carepoint
class FdbAllergenRelImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.allergen.rel'
    direct = [
        ('hic', 'carepoint_id'),
        (trim('hic_desc'), 'name'),
        ('hic', 'code'),
        ('hic_root', 'hic_root'),
        ('potentially_inactive', 'potentially_inactive'),
        ('ing_status', 'state'),
    ]


@carepoint
class FdbAllergenRelImporter(CarepointImporter):
    _model_name = 'carepoint.fdb.allergen.rel'
    _base_mapper = FdbAllergenRelImportMapper
