# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               changed_by,
                                               ExportMapper,
                                               )
from ..unit.backend_adapter import CarepointAdapter
from ..unit.mapper import CarepointImportMapper, trim
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import CarepointExporter

_logger = logging.getLogger(__name__)


class CarepointItem(models.Model):
    _name = 'carepoint.item'
    _inherits = {'medical.medicament': 'medicament_id'}

    medicament_id = fields.Many2one(
        string='Medicament',
        comodel_name='medical.medicament',
        ondelete='cascade',
        required=True,
    )
    ndc_id = fields.Many2one(
        string='NDC',
        comodel_name='fdb.ndc',
        required=True,
    )
    warehouse_id = fields.Many2one(
        string='Warehouse',
        comodel_name='stock.warehouse',
        required=True,
    )
    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.item',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )
    store_on_hand = fields.Float(
        compute="_compute_store_qty",
    )
    store_on_order = fields.Float(
        compute="_compute_store_qty",
    )
    trigger_export = fields.Boolean()

    @api.one
    def _compute_store_qty(self):
        context_product = self.with_context(warehouse=self.warehouse_id.id)
        avail = context_product._product_available()[self.id]
        self.store_on_hand = avail['qty_available']
        self.store_on_order = avail['incoming_qty']


class CarepointCarepointItem(models.Model):
    _name = 'carepoint.carepoint.item'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.item': 'odoo_id'}
    _description = 'Carepoint Item'
    _cp_lib = 'item'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='Item',
        comodel_name='carepoint.item',
        required=True,
        ondelete='restrict',
    )
    store_id = fields.Many2one(
        string='Store',
        comodel_name='carepoint.carepoint.store',
        readonly=True,
    )


class CarepointItemAdapter(CarepointAdapter):
    _model_name = 'carepoint.carepoint.item'


class CarepointItemBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Items.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.carepoint.item']


class CarepointItemImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.carepoint.item'

    direct = [
        (trim('DESCR'), 'name'),
        (trim('UPCCODE'), 'barcode'),
        ('add_date', 'created_at'),
        ('chg_date', 'updated_at'),
    ]

    @mapping
    def active(self, record):
        """Check if the product is active in Carepoint
        and set active flag in OpenERP
        status == 1 in Carepoint means active"""
        return {'active': (record.get('ACTIVE_YN') == 1)}

    @mapping
    def store_id(self, record):
        binder = self.binder_for('carepoint.carepoint.store')
        store_id = binder.to_odoo(record['store_id'])
        return {'store_id': store_id}

    @mapping
    def warehouse_id(self, record):
        binder = self.binder_for('carepoint.stock.warehouse')
        store_id = binder.to_odoo(record['store_id'])
        return {'warehouse_id': store_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['item_id']}

    @mapping
    @only_create
    def ndc_id(self, record):
        self._get_ndc(record)
        return {'ndc_id': ndc_id.id}

    @mapping
    @only_create
    def odoo_id(self, record):
        """ It binds on a medicament of an existing NDC """
        ndc = self._get_ndc(record)
        if ndc:
            return {'odoo_id': ndc.medicament_id.id}

    def _get_ndc(self, record):
        """ It returns the FDB NDC for the record. """
        return self.env['fdb.ndc'].search(
            [('name', '=', record['NDC'].strip())],
            limit=1,
        )


class CarepointItemImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.item']

    _base_mapper = CarepointItemImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['NDC'].strip(),
                                'carepoint.fdb.ndc.cs.ext')
        self._import_dependency(record['NDC'].strip(),
                                'carepoint.fdb.ndc')
        self._import_dependency(record['VENDOR'].strip(),
                                'carepoint.carepoint.vendor')


class CarepointItemExportMapper(ExportMapper):
    _model_name = 'carepoint.carepoint.item'

    direct = [
        ('name', 'DESCR'),
        ('barcode', 'UPCCODE'),
    ]

    @mapping
    @changed_by('active')
    def active_yn(self, binding):
        return {'ACTIVE_YN': binding.active}

    @mapping
    @changed_by('trigger_export')
    def export_quantities(self, binding):
        if binding.trigger_export:
            binding.trigger_export = False
            return {'ONHAND': binding.store_on_hand,
                    'ONORDER': binding.store_on_order,
                    }


class CarepointItemExporter(CarepointExporter):
    _model_name = ['carepoint.carepoint.item']
    _base_mapper = CarepointItemExportMapper
