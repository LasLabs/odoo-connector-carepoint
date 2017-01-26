# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, models, fields
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               none,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..backend import carepoint
from ..unit.mapper import (PartnerImportMapper,
                           trim,
                           CommonDateImporterMixer,
                           )
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

from ..connector import add_checkpoint


_logger = logging.getLogger(__name__)


class CarepointStore(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.store'
    _inherits = {'medical.pharmacy': 'pharmacy_id'}

    pharmacy_id = fields.Many2one(
        string='Pharmacy',
        comodel_name='medical.pharmacy',
        required=True,
        ondelete='cascade',
    )
    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.store',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )

    _sql_constraints = [
        ('pharmacy_unique', 'UNIQUE(pharmacy_id)',
         'This pharmacy already has an associated Carepoint Store'),
    ]

    @api.model_cr
    def get_by_pharmacy(self, pharmacy):
        """ It returns the store for the provided pharmacy """
        return self.search([
            ('pharmacy_id', '=', pharmacy.id),
        ])


class CarepointCarepointStore(models.Model):
    """ Binding Model for the Carepoint Store """
    _name = 'carepoint.carepoint.store'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.store': 'odoo_id'}
    _description = 'Carepoint Pharmacy (Store)'
    _cp_lib = 'store'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='carepoint.store',
        string='Company',
        required=True,
        ondelete='cascade'
    )
    warehouse_id = fields.Many2one(
        string='Warehouse',
        comodel_name='stock.warehouse',
    )


@carepoint
class CarepointStoreAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Store """
    _model_name = 'carepoint.carepoint.store'


@carepoint
class CarepointStoreBatchImporter(DelayedBatchImporter,
                                  CommonDateImporterMixer):
    """ Import the Carepoint Stores.
    For every company in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.store']


@carepoint
class CarepointStoreImportMapper(PartnerImportMapper):
    _model_name = 'carepoint.carepoint.store'

    direct = [
        (trim('name'), 'name'),
        (trim('fed_tax_id'), 'vat'),
        (trim('url'), 'website'),
        (trim('email'), 'email'),
        (none('nabp'), 'nabp_num'),
        (none('medcaid_no'), 'medicaid_num'),
        (none('NPI'), 'npi_num'),
        ('add_date', 'created_at'),
        ('chg_date', 'updated_at'),
    ]

    @mapping
    @only_create
    def odoo_id(self, record):
        """ Will bind the company or pharmacy on an existing pharmacy
        with the same name """
        domain = [('name', 'ilike', record.get('name', ''))]
        company_id = self.env['carepoint.store'].search(domain, limit=1)
        if not company_id:
            pharm = self.env['medical.pharmacy'].search(domain, limit=1)
            if pharm:
                company_id = self.env['carepoint.store'].create({
                    'pharmacy_id': pharm.id,
                })
        if company_id:
            return {'odoo_id': company_id.id}

    @mapping
    def parent_id(self, record):
        return {'parent_id': self.backend_record.company_id.partner_id.id}

    @mapping
    def warehouse_id(self, record):
        binder = self.binder_for('carepoint.stock.warehouse')
        warehouse_id = binder.to_odoo(record['store_id'])
        return {'warehouse_id': warehouse_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['store_id']}


@carepoint
class CarepointStoreImporter(CarepointImporter,
                             CommonDateImporterMixer):
    _model_name = ['carepoint.carepoint.store']
    _base_mapper = CarepointStoreImportMapper

    def _after_import(self, binding):
        self._import_dependency(binding.carepoint_id,
                                'carepoint.stock.warehouse')
        binder = self.binder_for('carepoint.stock.warehouse')
        warehouse_id = binder.to_odoo(binding.carepoint_id)
        binding.write({
            'warehouse_id': warehouse_id,
        })

    def _create(self, data):  # pragma: no cover
        binding = super(CarepointStoreImporter, self)._create(data)
        add_checkpoint(
            self.session, binding._name, binding.id, binding.backend_id.id
        )
        return binding
