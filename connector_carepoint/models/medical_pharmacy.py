# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..connector import get_environment
from ..backend import carepoint
from ..unit.mapper import PartnerImportMapper, trim, trim_and_titleize
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
         'A Carepoint binding for this partner already exists.'),
    ]


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

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        _logger.info('Search for carepoint companies %s returned %s\n',
                     filters, record_ids)
        for record_id in record_ids:
            _logger.info('In record loop with %s', record_id)
            self._import_record(record_id)


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

    @only_create
    @mapping
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
    def carepoint_id(self, record):
        return {'carepoint_id': record['store_id']}


@carepoint
class MedicalPharmacyImporter(CarepointImporter):
    _model_name = ['carepoint.medical.pharmacy']

    _base_mapper = MedicalPharmacyImportMapper

    def _create(self, data):
        binding = super(MedicalPharmacyImporter, self)._create(data)
        checkpoint = self.unit_for(MedicalPharmacyAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        # @TODO: Fix below error
        # 'csstore_addr' does not have the identity property.
        #  Cannot perform SET operation.
        #
        # self._import_dependency(record['store_id'],
        #                         'carepoint.carepoint.address.pharmacy')

    #
    # def _after_import(self, partner_binding):
    #     """ Import the addresses """
    #     book = self.unit_for(PartnerAddressBook, model='carepoint.address')
    #     book.import_addresses(self.carepoint_id, partner_binding.id)


@carepoint
class MedicalPharmacyAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.medical.pharmacy record """
    _model_name = ['carepoint.medical.pharmacy', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.core')
def company_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of companies modified on Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(MedicalPharmacyBatchImporter)
    importer.run(filters=filters)
