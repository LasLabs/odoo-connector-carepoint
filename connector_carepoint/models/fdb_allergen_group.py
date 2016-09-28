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


class CarepointFdbAllergenGroup(models.Model):
    _name = 'carepoint.fdb.allergen.group'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.allergen.group': 'odoo_id'}
    _description = 'Carepoint FdbAllergenGroup'
    _cp_lib = 'fdb_lbl_rid'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbAllergenGroup',
        comodel_name='fdb.allergen.group',
        required=True,
        ondelete='restrict'
    )


class FdbAllergenGroup(models.Model):
    _inherit = 'fdb.allergen.group'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.allergen.group',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbAllergenGroupAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.allergen.group'


@carepoint
class FdbAllergenGroupBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbAllergenGroups.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.allergen.group']


@carepoint
class FdbAllergenGroupImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.allergen.group'
    direct = [
        ('dam_agcsp', 'carepoint_id'),
        (trim('dam_agcspd'), 'name'),
        ('dam_agcsp', 'dam_code'),
        ('potentially_inactive', 'potentially_inactive'),
        ('dam_agcsp_status', 'state'),
    ]


@carepoint
class FdbAllergenGroupImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.allergen.group']
    _base_mapper = FdbAllergenGroupImportMapper
