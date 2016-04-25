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
from ..connector import get_environment
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

_logger = logging.getLogger(__name__)


class CarepointMedicalPrescriptionOrderLine(models.Model):
    """ Binding Model for the Carepoint Prescription """
    _name = 'carepoint.medical.prescription.order.line'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.prescription.order.line': 'odoo_id'}
    _description = 'Carepoint Prescription'
    _cp_lib = 'prescription'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='medical.prescription.order.line',
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
         'A Carepoint binding for this prescription already exists.'),
    ]


class MedicalPrescriptionOrderLine(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'medical.prescription.order.line'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.prescription.order.line',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class MedicalPrescriptionOrderLineAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Prescription """
    _model_name = 'carepoint.medical.prescription.order.line'


@carepoint
class MedicalPrescriptionOrderLineBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Prescriptions.
    For every prescription in the list, a delayed job is created.
    """
    _model_name = ['carepoint.medical.prescription.order.line']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class MedicalPrescriptionOrderLineImportMapper(ImportMapper):
    _model_name = 'carepoint.medical.prescription.order.line'

    direct = [
        ('ssn', 'ref'),
        ('email', 'email'),
        ('birth_date', 'dob'),
        ('death_date', 'dod'),
    ]

    @mapping
    def name(self, record):
        name = '%s %s' % (record.get('fname', ''),
                          record.get('lname', ''))
        return {'name': name}

    @mapping
    def gender(self, record):
        return {'gender': record.get('gender_cd').lower()}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['rx_id']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def physician_id(self, record):
        binder = self.binder_for('carepoint.medical.physician')
        binder.to_odoo(record['md_id'])
        return {'physician_id': ([4, record])}

    @mapping
    def patient_id(self, record):
        binder = self.binder_for('carepoint.medical.patient')
        binder.to_odoo(record['pat_id'])
        return {'patient_id': ([4, record])}

    @only_create
    @mapping
    def prescription_id(self, record):
        """ Will bind the prescription line on a existing prescription
        from same doctor and patient on the same date """
        physician_id = self.env
        prescription_id = self.env['medical.prescription.order'].search([
            ('name', '=', name),
            ('dob', '=', record.get('birth_date'))
        ],
            limit=1,
        )
        if prescription_id:
            return {'odoo_id': prescription_id.id}


@carepoint
class MedicalPrescriptionOrderLineImporter(CarepointImporter):
    _model_name = ['carepoint.medical.prescription.order.line']

    _base_mapper = MedicalPrescriptionOrderLineImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['pat_id'],
                                'carepoint.medical.patient')
        self._import_dependency(record['md_id'],
                                'carepoint.medical.physician')

    def _create(self, data):
        binding = super(MedicalPrescriptionOrderLineImporter, self)._create(data)
        checkpoint = self.unit_for(MedicalPrescriptionOrderLineAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    #
    # def _after_import(self, partner_binding):
    #     """ Import the addresses """
    #     book = self.unit_for(PartnerAddressBook, model='carepoint.address')
    #     book.import_addresses(self.carepoint_id, partner_binding.id)


@carepoint
class MedicalPrescriptionOrderLineAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.medical.prescription.order.line record """
    _model_name = ['carepoint.medical.prescription.order.line', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint')
def prescription_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of prescriptions modified on Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(MedicalPrescriptionOrderLineBatchImporter)
    importer.run(filters=filters)
