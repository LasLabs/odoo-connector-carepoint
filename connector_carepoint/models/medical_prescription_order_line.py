# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import re

from odoo import fields
from odoo import models
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               changed_by,
                                               ExportMapper,
                                               convert,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (CarepointImportMapper,
                           add_to,
                           CommonDateExportMapperMixer,
                           CommonDateImporterMixer,
                           CommonDateImportMapperMixer,
                           )
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import CarepointExporter

_logger = logging.getLogger(__name__)

try:
    from sqlalchemy import text, bindparam
except ImportError:
    _logger.debug('Unable to import SQLAlchemy resources')


class MedicalPrescriptionOrderLine(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'medical.prescription.order.line'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.rx.ord.ln',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointMedicalPrescriptionOrderLine(models.Model):
    """ Binding Model for the Carepoint Prescription """
    _name = 'carepoint.rx.ord.ln'
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


@carepoint
class MedicalPrescriptionOrderLineAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Prescription """
    _model_name = 'carepoint.rx.ord.ln'

    def _get_next_script_no(self, store_id, dea, otc=False):
        """ It generates and returns the next Rx ID in sequence
        Params:
            store_id (int): ID of the store in CarepPoint
            dea (int): DEA code for medicament
            otc (bool): True if medicament is OTC
        Return:
            (str) Newly generated script number
        """
        with self.carepoint.dbs['cph'].begin() as conn:
            with conn.begin():
                res = conn.execute(
                    text(
                        "SET NOCOUNT ON;"
                        "DECLARE @out VARCHAR(30);"
                        "EXEC CpGetScriptNo :store_id, "
                        ":dea, @out output, :otc;"
                        "SELECT @out;"
                        "SET NOCOUNT OFF;",
                        bindparams=[
                            bindparam('store_id'),
                            bindparam('dea'),
                            bindparam('otc'),
                        ],
                    ),
                    store_id=store_id,
                    dea=dea,
                    otc=otc,
                )
                id_int = res.fetchall()[0][0]
        return id_int

    def create(self, data):
        """ It gets the next Rx sequence, appends to data, and calls super """
        data['script_no'] = self._get_next_script_no(
            data['store_id'], data['drug_dea_class'],
        )
        return super(MedicalPrescriptionOrderLineAdapter, self).create(data)


@carepoint
class MedicalPrescriptionOrderLineBatchImporter(DelayedBatchImporter,
                                                CommonDateImporterMixer):
    """ Import the Carepoint Prescriptions.
    For every prescription in the list, a delayed job is created.
    """
    _model_name = ['carepoint.rx.ord.ln']


@carepoint
class MedicalPrescriptionOrderLineImportMapper(CarepointImportMapper,
                                               CommonDateImportMapperMixer):
    _model_name = 'carepoint.rx.ord.ln'

    direct = [
        (convert('start_date', fields.Datetime.to_string),
         'date_start_treatment'),
        (convert('expire_date', fields.Datetime.to_string),
         'date_stop_treatment'),
        ('written_qty', 'qty'),
        ('freq_of_admin', 'frequency'),
        (add_to('refills_left', -1), 'refill_qty_remain'),
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
    def quantity(self, record):
        return {
            'quantity': re.sub(r'[^0-9]', '', record['units_entered']),
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
        fdb_ndc = binder.to_odoo(record['ndc'].strip(), browse=True)
        return {'ndc_id': fdb_ndc.ndc_id.id}

    @mapping
    @only_create
    def gcn_id(self, record):
        binder = self.binder_for('carepoint.fdb.gcn')
        fdb_gcn = binder.to_odoo(record['gcn_seqno'], browse=True)
        return {'gcn_id': fdb_gcn.gcn_id.id}

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
class MedicalPrescriptionOrderLineImporter(CarepointImporter,
                                           CommonDateImporterMixer):
    _model_name = ['carepoint.rx.ord.ln']

    _base_mapper = MedicalPrescriptionOrderLineImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['rx_id'],
                                'carepoint.medical.prescription.order')
        self._import_dependency(record['ndc'],
                                'carepoint.fdb.ndc')


@carepoint
class MedicalPrescriptionOrderLineExportMapper(ExportMapper,
                                               CommonDateExportMapperMixer):
    _model_name = 'carepoint.rx.ord.ln'

    direct = [
        (convert('date_start_treatment', fields.Datetime.from_string),
         'start_date'),
        (convert('date_stop_treatment', fields.Datetime.from_string),
         'expire_date'),
        ('qty', 'written_qty'),
        ('frequency', 'freq_of_admin'),
        ('quantity', 'units_entered'),
        ('refill_qty_original', 'refills_orig'),
        (add_to('refill_qty_remain', 1), 'refills_left'),
    ]

    @mapping
    @changed_by('patient_id')
    def pat_id(self, record):
        record = record.patient_id.carepoint_bind_ids.filtered(
            lambda r: r.backend_id == self.backend_record,
        )
        return {'pat_id': record.carepoint_id}

    @mapping
    @changed_by('prescription_order_id.partner_id')
    def store_id(self, record):
        partner = record.prescription_order_id.partner_id
        record = self.env['carepoint.carepoint.store'].search([
            ('partner_id', '=', partner.id),
            ('backend_id', '=', self.backend_record.id),
        ],
            limit=1,
        )
        return {'store_id': record.carepoint_id or 1}

    @mapping
    @changed_by('physician_id')
    def md_id(self, record):
        physician = record.prescription_order_id.physician_id
        record = physician.carepoint_bind_ids.filtered(
            lambda r: r.backend_id == self.backend_record,
        )
        return {'md_id': record.carepoint_id}

    @mapping
    @changed_by('ndc_id')
    def ndc(self, record):
        if not record.ndc_id:
            ndcs = self.env['carepoint.item'].search(
                [('medicament_id', '=', record.medicament_id.id)],
            )
            record.ndc_id = ndcs.ordered(lambda r: r.store_on_hand)[0]
        return {'ndc': record.ndc_id.name}

    @mapping
    @changed_by('gcn_id')
    def gcn_seqno(self, record):
        record = self.env['carepoint.fdb.gcn'].search([
            ('backend_id', '=', self.backend_record.id),
            ('gcn_id', '=', record.gcn_id.id),
        ],
            limit=1,
        )
        return {'gcn_seqno': record.carepoint_id}

    @mapping
    @changed_by('ndc_id')
    def mfg(self, record):
        binder = self.binder_for('carepoint.fdb.img.mfg')
        fdb_ndc_id = self.env['carepoint.fdb.ndc'].search([
            ('odoo_id', '=', record.ndc_id.id),
        ],
            limit=1,
        )
        mfg = binder.to_backend(fdb_ndc_id.lbl_mfg_id.mfg)
        return {'mfg': mfg}

    @mapping
    @changed_by('medicament_id')
    def medicament_meta(self, record):
        return {'drug_name': record.medicament_id.display_name,
                'gpi_rx': record.medicament_id.gpi,
                'drug_dea_class': record.medicament_id.control_code,
                }

    @mapping
    @changed_by('medication_dosage_id')
    def sig_code_and_text(self, record):
        return {'sig_code': record.medication_dosage_id.code,
                'sig_text': record.medication_dosage_id.name,
                'sig_text_english': record.medication_dosage_id.name,
                }

    @mapping
    @changed_by('last_dispense_id')
    def last_rxdisp_and_meta(self, record):
        if not record.last_dispense_id:
            return
        proc = record.last_dispense_id.carepoint_bind_ids[0]
        return {'last_rxdisp_id': proc.carepoint_id,
                'last_refill_qty': proc.product_qty,
                'last_refill_date': proc.date_planned,
                'last_dispense_prod': proc.product_id.display_name,
                }

    @mapping
    @changed_by('prescription_order_id.transfer_pharmacy_id')
    def src_org_id(self, record):
        pharmacy = record.prescription_order_id.transfer_pharmacy_id
        record = self.env['carepoint.org.bind'].search([
            ('pharmacy_id', '=', pharmacy.id),
            ('backend_id', '=', self.backend_record.id),
        ],
            limit=1,
        )
        return {'src_org_id': record.id}

    @mapping
    @changed_by('is_substitutable')
    def daw_yn(self, record):
        return {'daw_yn': not record.is_substitutable}

    @mapping
    def static_defaults(self, record):
        return {
            'df': 1,
            'uu': 0,
            'dosage_multiplier': 1,
            'app_flags': 0,
            'treatment_yn': 0,
            'workflow_status_cn': 0,
            'taxable': 0,
            'priority_cn': 0,
            'rxq_status_cn': 0,
        }


@carepoint
class MedicalPrescriptionOrderLineExporter(CarepointExporter):
    _model_name = ['carepoint.rx.ord.ln']
    _base_mapper = MedicalPrescriptionOrderLineExportMapper

    def _export_dependencies(self):
        self._export_dependency(
            self.binding_record.patient_id,
            'carepoint.medical.patient',
            force=True,
        )
        self._export_dependency(
            self.binding_record.prescription_order_id.physician_id,
            'carepoint.medical.physician',
            force=True,
        )
        self._export_dependency(
            self.binding_record.prescription_order_id.transfer_pharmacy_id,
            'carepoint.org.bind',
            force=True,
        )
