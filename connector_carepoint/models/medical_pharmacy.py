# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..backend import carepoint
from ..unit.mapper import PartnerImportMapper
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

from ..connector import add_checkpoint


_logger = logging.getLogger(__name__)


class CarepointMedicalPharmacy(models.Model):
    """ Binding Model for the Carepoint Store """
    _name = 'carepoint.medical.pharmacy'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.pharmacy': 'odoo_id'}
    _description = 'Carepoint Pharmacy (Store)'
    _cp_lib = 'store'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='medical.pharmacy',
        string='Company',
        required=True,
        ondelete='cascade'
    )
    warehouse_id = fields.Many2one(
        string='Warehouse',
        comodel_name='stock.warehouse',
    )


class MedicalPharmacy(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'medical.pharmacy'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.pharmacy',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class MedicalPharmacyAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Store """
    _model_name = 'carepoint.medical.pharmacy'


@carepoint
class MedicalPharmacyBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Stores.
    For every company in the list, a delayed job is created.
    """
    _model_name = ['carepoint.medical.pharmacy']


@carepoint
class MedicalPharmacyImportMapper(PartnerImportMapper):
    _model_name = 'carepoint.medical.pharmacy'

    direct = [
        ('name', 'name'),
        ('fed_tax_id', 'vat'),
        ('url', 'website'),
        ('email', 'email'),
        ('nabp', 'nabp_num'),
        ('medcaid_no', 'medicaid_num'),
        ('NPI', 'npi_num'),
        ('add_date', 'created_at'),
        ('chg_date', 'updated_at'),
    ]

    @mapping
    @only_create
    def odoo_id(self, record):
        """ Will bind the company on an existing company
        with the same name """
        company_id = self.env['medical.pharmacy'].search(
            [('name', 'ilike', record.get('name', ''))],
            limit=1,
        )
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
class MedicalPharmacyImporter(CarepointImporter):
    _model_name = ['carepoint.medical.pharmacy']
    _base_mapper = MedicalPharmacyImportMapper

    def _after_import(self, binding):
        self._import_dependency(binding.carepoint_id,
                                'carepoint.stock.warehouse')
        binder = self.binder_for('carepoint.stock.warehouse')
        warehouse_id = binder.to_odoo(binding.carepoint_id)
        binding.write({
            'warehouse_id': warehouse_id,
        })

    def _create(self, data):
        binding = super(MedicalPharmacyImporter, self)._create(data)
        add_checkpoint(
            self.session, binding._name, binding.id, binding.backend_id.id
        )
        return binding
