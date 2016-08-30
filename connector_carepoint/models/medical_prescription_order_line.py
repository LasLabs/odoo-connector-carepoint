# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import fields
from openerp import models
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

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
        ('refills_orig', 'refill_qty_original')
    ]

    @mapping
    def name(self, record):
        name = '{prefix}{name}'.format(
            prefix=self.backend_record.rx_prefix,
            name=record['script_no'],
        )
        return {'name': name}

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
        sig_text = record['sig_text_english'].strip()
        dose_id = dose_obj.search([
            '|',
            ('name', '=', sig_text),
            ('code', '=', sig_code),
        ],
            limit=1,
        )
        if not len(dose_id):
            dose_id = dose_obj.create({
                'name': sig_text,
                'code': sig_code,
            })
        return {'medication_dosage_id': dose_id[0].id}

    @mapping
    @only_create
    def duration_uom_id(self, record):
        # @TODO: make this use self.env.ref to core days - verify it exists
        uom_id = self.env['product.uom'].search(
            [('name', '=', 'DAYS')], limit=1,
        )
        return {'duration_uom_id': uom_id.id}

    @mapping
    def physician_id(self, record):
        binder = self.binder_for('carepoint.medical.physician')
        physician_id = binder.to_odoo(record['md_id'])
        return {'physician_id': physician_id}

    @mapping
    def prescription_order_id(self, record):
        binder = self.binder_for('carepoint.medical.prescription.order')
        prescription_order_id = binder.to_odoo(record['rx_id'])
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
