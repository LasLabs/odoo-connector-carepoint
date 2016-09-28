# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class CarepointFdbAllergen(models.Model):
    _name = 'carepoint.fdb.allergen'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.allergen': 'odoo_id'}
    _description = 'Carepoint FdbAllergen'
    _cp_lib = 'fdb_allergen'

    odoo_id = fields.Many2one(
        string='FdbAllergen',
        comodel_name='fdb.allergen',
        required=True,
        ondelete='restrict'
    )


class FdbAllergen(models.Model):
    _inherit = 'fdb.allergen'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.allergen',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbAllergenAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.allergen'


@carepoint
class FdbAllergenBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbAllergens.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = 'carepoint.fdb.allergen'


@carepoint
class FdbAllergenImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.allergen'
    direct = [
        ('hicl_rel_no', 'hicl_rel_no'),
        ('hic', 'code'),
    ]

    @mapping
    def carepoint_id(self, record):
        out = '%s,%s' % (record['hicl_seqno'], record['hic_seqn'])
        return {'carepoint_id': out}


@carepoint
class FdbAllergenImporter(CarepointImporter):
    _model_name = 'carepoint.fdb.allergen'
    _base_mapper = FdbAllergenImportMapper
