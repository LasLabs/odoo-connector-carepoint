# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import re

from os import path

from odoo import models, fields
from odoo.addons.connector_v9.unit.mapper import (mapping,
                                               only_create,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (BaseImportMapper,
                           trim,
                           )
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

try:
    from pint import (DimensionalityError,
                      LazyRegistry,
                      UndefinedUnitError,
                      )
    from pint.util import infer_base_unit
    ureg = LazyRegistry()
    ureg.load_definitions(
        path.abspath(
            path.join(
                path.dirname(__file__),
                '..',
                'data',
                'medical_units.txt',
            )
        )
    )
except ImportError:
    ureg = None


_logger = logging.getLogger(__name__)


class FdbUnit(models.Model):
    _inherit = 'fdb.unit'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.unit',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointFdbUnit(models.Model):
    _name = 'carepoint.fdb.unit'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.unit': 'odoo_id'}
    _description = 'Carepoint FdbUnit'
    _cp_lib = 'fdb_unit'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbUnit',
        comodel_name='fdb.unit',
        required=True,
        ondelete='restrict'
    )


@carepoint
class FdbUnitAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.unit'


@carepoint
class FdbUnitBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbUnits.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.unit']


@carepoint
class FdbUnitImportMapper(BaseImportMapper):
    _model_name = 'carepoint.fdb.unit'
    direct = [
        (trim('str30'), 'str30'),
        (trim('str60'), 'str60'),
        ('update_yn', 'update_yn'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['str'].strip()}

    def _uom_category_id(self, unit_root_str):
        """ Find or create a UOM category """
        categ_obj = self.env['product.uom.categ']
        if unit_root_str == 'day':
            return self.env.ref('product_uom.product_uom_category_time')
        categ_id = categ_obj.search([
            ('name', '=', unit_root_str),
        ],
            limit=1,
        )
        if not len(categ_id):
            categ_id = categ_obj.create({
                'name': unit_root_str,
            })
        return categ_id

    @mapping
    @only_create
    def uom_id(self, record):

        str60 = self._parse_str60(record['str60'])

        try:
            unit_base = ureg(str60)
            unit_base_str = str(unit_base.u)
            unit_root = infer_base_unit(unit_base)
            unit_root_str = str(unit_root)
            unit_converted = unit_base.to(unit_root)
        except (DimensionalityError, UndefinedUnitError):
            _logger.info(
                'Could not parse unit "%s". Inferring as base unit.',
            )
            unit_base = unit_base_str = record['str']
            unit_root = unit_root_str = unit_base

        categ_id = self._uom_category_id(unit_root_str)

        uom_obj = self.env['product.uom']
        uom_id = uom_obj.search([
            ('name', '=', unit_base_str),
        ])
        if len(uom_id):
            return {'uom_id': uom_id[0].id}

        vals = {
            'name': record['str'].strip(),
            'category_id': categ_id.id,
        }

        if unit_base == unit_root:
            vals['uom_type'] = 'reference'
        elif unit_converted.m < 1:
            factor = float(unit_base.m) / float(unit_converted.m)
            if unit_base.m != 1:
                factor /= unit_base.m
            vals.update({
                'uom_type': 'smaller',
                'factor': factor,
            })
        else:
            factor = float(unit_converted.m) / float(unit_base.m)
            if unit_base.m != 1:
                factor *= unit_base.m
            vals.update({
                'uom_type': 'bigger',
                'factor_inv': factor,
            })
        return vals

    def _parse_str60(self, str60):
        """ It parses the str60 to fix edge cases """

        str60 = str60.strip()

        # Handle CCs
        match = re.search(r'(?P<unit>\d+)cc', str60, re.IGNORECASE)
        if match:
            return '%s cc' % match.group('unit')

        # Handle daysx
        match = re.search(r'daysx(?P<unit>\d+)', str60, re.IGNORECASE)
        if match:
            return 'days ** %s' % match.group('unit')

        return str60

    # @mapping
    # @only_create
    # def unit_id(self, record):
    #     """ Will bind the unit on a existing unit with same name """
    #     unit_id = self.env['medical.drug.unit'].search([
    #         ('name', 'ilike', record['gcdf_desc'].strip()),
    #     ],
    #         limit=1,
    #     )
    #     if unit_id:
    #         return {'unit_id': unit_id.id}


@carepoint
class FdbUnitImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.unit']
    _base_mapper = FdbUnitImportMapper
