# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  ImportMapper
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (PersonImportMapper,
                           PersonExportMapper,
                           trim,
                           trim_and_titleize,
                          )
from ..connector import get_environment
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

_logger = logging.getLogger(__name__)


class CarepointMedicalPhysician(models.Model):
    """ Binding Model for the Carepoint Physicians """
    _name = 'carepoint.medical.physician'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.physician': 'odoo_id'}
    _description = 'Carepoint Physician'
    _cp_lib = 'doctor'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='medical.physician',
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
         'A Carepoint binding for this physician already exists.'),
    ]


class MedicalPhysician(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'medical.physician'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.physician',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class MedicalPhysicianAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Physician """
    _model_name = 'carepoint.medical.physician'


@carepoint
class MedicalPhysicianBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Physicians.
    For every physician in the list, a delayed job is created.
    """
    _model_name = ['carepoint.medical.physician']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class MedicalPhysicianImportMapper(PersonImportMapper):
    _model_name = 'carepoint.medical.physician'

    direct = [
        (trim('email'), 'email'),
        (trim('url'), 'website'),
        (trim('dea_no'), 'dea_num'),
        (trim('fed_tax_id'), 'vat'),
        (trim('stat_lic_id'), 'license_num'),
        (trim('npi_id'), 'npi_num'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['md_id']}

    @only_create
    @mapping
    def odoo_id(self, record):
        """ Will bind the physician on a existing physician
        with the same name & email """
        name = self._get_name(record)
        physician_id = self.env['medical.physician'].search([
            ('name', 'ilike', name),
            ('email', 'ilike', record.get('email')),
        ],
            limit=1,
        )
        if physician_id:
            return {'odoo_id': physician_id.id}


@carepoint
class MedicalPhysicianImporter(CarepointImporter):
    _model_name = ['carepoint.medical.physician']

    _base_mapper = MedicalPhysicianImportMapper

    def _create(self, data):
        binding = super(MedicalPhysicianImporter, self)._create(data)
        checkpoint = self.unit_for(MedicalPhysicianAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    #
    # def _after_import(self, partner_binding):
    #     """ Import the addresses """
    #     book = self.unit_for(PartnerAddressBook, model='carepoint.address')
    #     book.import_addresses(self.carepoint_id, partner_binding.id)


@carepoint
class MedicalPhysicianAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.medical.physician record """
    _model_name = ['carepoint.medical.physician', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.physician')
def physician_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of physicians modified on Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(MedicalPhysicianBatchImporter)
    importer.run(filters=filters)
