# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields, api
from openerp.exceptions import ValidationError
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
        string='Prescription Line',
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
class MedicalPrescriptionOrderLineImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.medical.prescription.order.line'

    direct = [
        ('start_date', 'date_start_treatment'),
        ('expire_date', 'date_stop_treatment'),
        ('written_qty', 'qty'),
        ('freq_of_admin', 'frequency'),
        ('units_entered', 'quantity'),
        ('refills_left', 'refill_qty_remain'),
    ]

    @mapping
    def name(self, record):
        name = '{prefix}{name}'.format(
            prefix=self.backend_record.rx_prefix,
            name=record['script_no'],
        )
        return {'name': name}

    @mapping
    def refill_qty_original(self, record):
        return {'refill_qty_original': (record['refills_orig'] or 0) + 1}

    @mapping
    @only_create
    def duration(self, record):
        days_supply = record['days_supply'] or 0
        refills = (record['refills_orig'] or 0) + 1
        duration = days_supply * refills
        return {'duration': duration}

    @mapping
    @only_create
    def medicament_and_meta(self, record):
        binder = self.binder_for('carepoint.fdb.ndc')
        ndc_id = binder.to_odoo(record['ndc'], browse=True)
        return {'medicament_id': ndc_id.medicament_id.id,
                'dose_uom_id': ndc_id.medicament_id.uom_id.id,
                'dispense_uom_id': ndc_id.medicament_id.uom_id.id,
                }

    @mapping
    def is_substitutable(self, record):
        return {'is_substitutable': not bool(record['daw_yn'])}

    @mapping
    def patient_id(self, record):
        binder = self.binder_for('carepoint.medical.patient')
        patient_id = binder.to_odoo(record['pat_id'])
        return {'patient_id': patient_id}

    @mapping
    @only_create
    def ndc_id(self, record):
        binder = self.binder_for('carepoint.fdb.ndc')
        ndc_id = binder.to_odoo(record['ndc'].strip())
        return {'ndc_id': ndc_id}

    @mapping
    @only_create
    def gcn_id(self, record):
        binder = self.binder_for('carepoint.fdb.gcn')
        gcn_id = binder.to_odoo(record['gcn_seqno'])
        return {'gcn_id': gcn_id}

    @mapping
    @only_create
    def medication_dosage_id(self, record):
        # @TODO: Find sig codes table & integrate instead of search
        dose_obj = self.env['medical.medication.dosage']
        sig_code = record['sig_code'].strip()
        dose_id = dose_obj.search(['|',
            ('name', '=', record['sig_text_english'].strip()),
            ('code', '=', sig_code),
        ],
            limit=1,
        )
        if not len(dose_id):
            dose_id = dose_obj.create({
                'name': record['sig_text_english'].strip(),
                'code': sig_code,
            })
        return {'medication_dosage_id': dose_id.id}

    @mapping
    @only_create
    def duration_uom_id(self, record):
        uom_id = self.env['product.uom'].search(
            [('name', '=', 'DAYS')], limit=1,
        )
        return {'duration_uom_id': uom_id.id}

    @mapping
    def physician_id(self, record):
        binder = self.binder_for('carepoint.medical.physician')
        physician_id = binder.to_odoo(record['md_id'], True)
        return {'physician_id': physician_id}

    @mapping
    def prescription_order_id(self, record):
        binder = self.binder_for('carepoint.medical.prescription.order')
        prescription_order_id = binder.to_odoo(record['rx_id'], True)
        return {'prescription_order_id': prescription_order_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['rx_id']}


@carepoint
class MedicalPrescriptionOrderLineImporter(CarepointImporter):
    _model_name = ['carepoint.medical.prescription.order.line']

    _base_mapper = MedicalPrescriptionOrderLineImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['rx_id'],
                                'carepoint.medical.prescription.order')
        self._import_dependency(record['ndc'],
                                'carepoint.fdb.ndc')

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
class MedicalPrescriptionOrderLineExportMapper(ExportMapper):
    _model_name = 'carepoint.medical.prescription.order.line'

    direct = [
        ('date_start_treatment', 'start_date'),
        ('date_stop_treatment', 'expire_date'),
        ('qty', 'written_qty'),
        ('frequency', 'freq_of_admin'),
        ('quantity', 'units_per_dose'),
        # Note that the col naming seems to be reversed *shrug*
        # ('refill_qty_original', 'refills_left'),
        # ('refill_qty_remain', 'refills_orig'),
    ]

    @mapping
    def pat_id(self, record):
        return {'pat_id': record.carepoint_id}

    @mapping
    @changed_by('gender')
    def gender_cd(self):
        return {'gender_cd': record.get('gender').upper()}


@carepoint
class MedicalPrescriptionOrderLineExporter(CarepointExporter):
    _model_name = ['carepoint.medical.prescription.order.line']
    _base_mapper = MedicalPrescriptionOrderLineExportMapper


@carepoint
class MedicalPrescriptionOrderLineAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.medical.prescription.order.line record """
    _model_name = ['carepoint.medical.prescription.order.line', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.prescription')
def prescription_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of prescriptions modified on Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(MedicalPrescriptionOrderLineBatchImporter)
    importer.run(filters=filters)
