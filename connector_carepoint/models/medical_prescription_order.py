# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, fields, models
from odoo.addons.connector_v9.unit.mapper import (mapping,
                                               ExportMapper,
                                               none,
                                               convert,
                                               backend_to_m2o,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (CarepointImportMapper,
                           CommonDateExportMapperMixer,
                           CommonDateImporterMixer,
                           CommonDateImportMapperMixer,
                           )
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import (CarepointExporter)

_logger = logging.getLogger(__name__)


class MedicalPrescriptionOrder(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'medical.prescription.order'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.medical.prescription.order',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )
    carepoint_store_id = fields.Many2one(
        string='Carepoint Store',
        comodel_name='carepoint.store',
        compute='_compute_carepoint_store_id',
        store=True,
    )

    @api.multi
    def _compute_carepoint_store_id(self):
        for rec_id in self:
            store = rec_id.carepoint_store_id.get_by_pharmacy(
                rec_id.partner_id,
            )
            rec_id.carepoint_store_id = store.id


class CarepointMedicalPrescriptionOrder(models.Model):
    """ Binding Model for the Carepoint Prescription """
    _name = 'carepoint.medical.prescription.order'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.prescription.order': 'odoo_id'}
    _description = 'Carepoint Prescription'
    _cp_lib = 'prescription'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='medical.prescription.order',
        string='Prescription Line',
        required=True,
        ondelete='cascade'
    )


@carepoint
class MedicalPrescriptionOrderAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Prescription """
    _model_name = 'carepoint.medical.prescription.order'


@carepoint
class MedicalPrescriptionOrderBatchImporter(DelayedBatchImporter,
                                            CommonDateImporterMixer):
    """ Import the Carepoint Prescriptions.
    For every prescription in the list, a delayed job is created.
    """
    _model_name = ['carepoint.medical.prescription.order']


@carepoint
class MedicalPrescriptionOrderImportMapper(CarepointImportMapper,
                                           CommonDateImportMapperMixer):
    _model_name = 'carepoint.medical.prescription.order'

    direct = [
        ('start_date', 'date_prescription'),
        ('rx_id', 'carepoint_id'),
        (backend_to_m2o('pat_id', binding='carepoint.medical.patient'),
         'patient_id'),
        (backend_to_m2o('md_id', binding='carepoint.medical.physician'),
         'physician_id'),
    ]

    @mapping
    def active(self, record):
        return {'active': record['status_cn'] == 3}

    @mapping
    def partner_id(self, record):
        binder = self.binder_for('carepoint.carepoint.store')
        store = binder.to_odoo(record['store_id'], browse=True)
        return {'partner_id': store.pharmacy_id.id}


@carepoint
class MedicalPrescriptionOrderImporter(CarepointImporter,
                                       CommonDateImporterMixer):
    _model_name = ['carepoint.medical.prescription.order']
    _base_mapper = MedicalPrescriptionOrderImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['pat_id'],
                                'carepoint.medical.patient')
        self._import_dependency(record['md_id'],
                                'carepoint.medical.physician')


@carepoint
class MedicalPrescriptionOrderExportMapper(ExportMapper,
                                           CommonDateExportMapperMixer):
    _model_name = 'carepoint.medical.prescription.order'

    direct = [
        (convert('date_prescription', fields.Datetime.from_string),
         'start_date'),
        ('carepoint_id', 'pat_id'),
        (none('qty'), 'written_qty'),
        (none('frequency'), 'freq_of_admin'),
        (none('quantity'), 'units_per_dose'),
        # Note that the col naming seems to be reversed *shrug*
        # ('refill_qty_original', 'refills_left'),
        # ('refill_qty_remain', 'refills_orig'),
    ]

    @mapping
    def status_cn(self, record):
        if not record.active:
            return {'status_cn': 3}


@carepoint
class MedicalPrescriptionOrderExporter(CarepointExporter):
    _model_name = ['carepoint.medical.prescription.order']
    _base_mapper = MedicalPrescriptionOrderExportMapper
