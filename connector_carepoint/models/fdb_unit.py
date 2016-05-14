# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from os import path
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  ImportMapper
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (CarepointImportMapper,
                           trim,
                           trim_and_titleize,
                           to_ord,
                          )
from ..connector import get_environment
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

from pint import LazyRegistry
from pint.util import infer_base_unit

_logger = logging.getLogger(__name__)


ureg = LazyRegistry()
ureg.load_definitions(path.abspath(path.join(
    path.dirname(__file__), '..', 'data', 'medical_units.txt',
)))


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

class FdbUnit(models.Model):
    _inherit = 'fdb.unit'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.unit',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
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

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbUnitImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.unit'
    direct = [
        (trim('str30'), 'str30'),
        (trim('str60'), 'str60'),
        ('update_yn', 'update_yn'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['str'].strip()}

    @mapping
    @only_create
    def uom_id(self, record):

        unit_base = ureg(record['str60'].strip())
        unit_base_str = str(unit_base.u)
        unit_root = infer_base_unit(unit_base)
        unit_root_str = str(unit_root)
        unit_converted = unit_base.to(unit_root)

        categ_obj = self.env['product.uom.categ']
        categ_id = categ_obj.search([
            ('name', '=', unit_root_str),
        ],
            limit=1,
        )
        if not len(categ_id):
            categ_id = categ_obj.create({
                'name': unit_root_str,
            })

        uom_obj = self.env['product.uom']
        uom_id = uom_obj.search([
            ('name', '=', unit_base_str),
        ])
        if len(uom_id):
            return {'uom_id': uom_id.id}

        vals = {
            'name': record['str'].strip(),
            'category_id': categ_id.id,
        }

        if unit_base == unit_root:
            vals['uom_type'] = 'reference'
        elif unit_converted.m < 0:
            factor = float(unit_base.m) / float(unit_converted.m)
            if unit_base.m != 1:
                factor *= unit_base.m
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
                'factor': factor,
            })
        return vals

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


@job(default_channel='root.carepoint.fdb')
def fdb_unit_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of Units from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbUnitBatchImporter)
    importer.run(filters=filters)
