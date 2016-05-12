# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  changed_by,
                                                  only_create,
                                                  ExportMapper,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..connector import get_environment
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import (CarepointExporter)
from ..unit.delete_synchronizer import (CarepointDeleter)
from ..connector import add_checkpoint, get_environment
from ..related_action import unwrap_binding
from .procurement_order import ProcurementOrderUnit
from .sale_order_line import SaleOrderLineUnit


_logger = logging.getLogger(__name__)


class CarepointSaleOrder(models.Model):
    """ Binding Model for the Carepoint Patient """
    _name = 'carepoint.sale.order'
    _inherit = 'carepoint.binding'
    _inherits = {'sale.order': 'odoo_id'}
    _description = 'Carepoint Sale'
    _cp_lib = 'order'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='sale.order',
        string='Company',
        required=True,
        ondelete='cascade'
    )
    backend_id = fields.Many2one(
        comodel_name='carepoint.backend',
        string='Carepoint Backend',
        store=True,
        readonly=True,
        # override 'carepoint.binding', can't be INSERTed if True:
        required=False,
    )
    created_at = fields.Date('Created At (on Carepoint)')
    updated_at = fields.Date('Updated At (on Carepoint)')

    _sql_constraints = [
        ('odoo_uniq', 'unique(backend_id, odoo_id)',
         'A Carepoint binding for this order already exists.'),
    ]


class SaleOrder(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'sale.order'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.sale.order',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class SaleOrderAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Patient """
    _model_name = 'carepoint.sale.order'


@carepoint
class SaleOrderBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Patients.
    For every order in the list, a delayed job is created.
    """
    _model_name = ['carepoint.sale.order']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class SaleOrderImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.sale.order'

    @mapping
    def date_order(self, record):
        if record['submit_date']:
            return {'date_order': record['submit_date']}
        return {'date_order': record['add_date']}

    @mapping
    def partner_data(self, record):
        binder = self.binder_for('carepoint.carepoint.account')
        if record['acct_id']:
            acct_id = binder.to_odoo(record['acct_id'])
            acct_id = self.env['carepoint.account'].browse(acct_id)
            patient_id = acct_id.patient_id
        else:
            patient_id = self.env.ref('connector_carepoint.patient_null')
        partner_id = patient_id.commercial_partner_id
        return {'partner_id': partner_id.id,
                'payment_term_id': partner_id.property_payment_term_id.id,
                }

    @mapping
    def pharmacy_id(self, record):
        binder = self.binder_for('carepoint.medical.pharmacy')
        store_id = binder.to_odoo(record['store_id'])
        return {'pharmacy_id': store_id}
    
    @mapping
    # @only_create
    def state(self, record):
        state_id = self.env.ref(
            'connector_carepoint.state_%d' % record['order_state_cn']
        )
        return {'state': state_id.order_state}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['order_id']}


@carepoint
class SaleOrderImporter(CarepointImporter):
    _model_name = ['carepoint.sale.order']

    _base_mapper = SaleOrderImportMapper

    def _create(self, data):
        binding = super(SaleOrderImporter, self)._create(data)
        checkpoint = self.unit_for(SaleOrderAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['acct_id'],
                                'carepoint.carepoint.account')

    def _after_import(self, binding):
        """ Import the sale lines & procurements """
        line_unit = self.unit_for(
            SaleOrderLineUnit, model='carepoint.sale.order.line',
        )
        line_unit._import_sale_order_lines(
            self.carepoint_id, binding.id,
        )
        proc_unit = self.unit_for(
            ProcurementOrderUnit, model='carepoint.procurement.order',
        )
        proc_unit._import_procurements_for_sale(
            self.carepoint_id, binding.id,
        )


@carepoint
class SaleOrderExportMapper(ExportMapper):
    _model_name = 'carepoint.sale.order'

    direct = [
        ('ref', 'ssn'),
        ('email', 'email'),
        ('dob', 'birth_date'),
        ('dod', 'death_date'),
    ]

    @mapping
    def pat_id(self, record):
        return {'pat_id': record.carepoint_id}

    @changed_by('gender')
    @mapping
    def gender_cd(self):
        return {'gender_cd': record.get('gender').upper()}


@carepoint
class SaleOrderExporter(CarepointExporter):
    _model_name = ['carepoint.sale.order']
    _base_mapper = SaleOrderExportMapper


@carepoint
class SaleOrderDeleteSynchronizer(CarepointDeleter):
    _model_name = ['carepoint.sale.order']


@carepoint
class SaleOrderAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.sale.order record """
    _model_name = ['carepoint.sale.order', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)
