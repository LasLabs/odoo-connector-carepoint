# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import fields
from openerp import models
from openerp.addons.connector.unit.mapper import (mapping,
                                                  ExportMapper,
                                                  none,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..unit.export_synchronizer import (CarepointExporter)

_logger = logging.getLogger(__name__)


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


@carepoint
class MedicalPrescriptionOrderAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Prescription """
    _model_name = 'carepoint.medical.prescription.order'


@carepoint
class MedicalPrescriptionOrderBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Prescriptions.
    For every prescription in the list, a delayed job is created.
    """
    _model_name = ['carepoint.medical.prescription.order']


@carepoint
class MedicalPrescriptionOrderImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.medical.prescription.order'

    direct = []

    @mapping
    def patient_id(self, record):
        binder = self.binder_for('carepoint.medical.patient')
        patient_id = binder.to_odoo(record['pat_id'])
        return {'patient_id': patient_id}

    @mapping
    def physician_id(self, record):
        binder = self.binder_for('carepoint.medical.physician')
        physician_id = binder.to_odoo(record['md_id'])
        return {'physician_id': physician_id}

    @mapping
    def partner_id(self, record):
        binder = self.binder_for('carepoint.carepoint.store')
        pharmacy_id = binder.to_odoo(record['store_id'])
        return {'partner_id': pharmacy_id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['rx_id']}


@carepoint
class MedicalPrescriptionOrderImporter(CarepointImporter):
    _model_name = ['carepoint.medical.prescription.order']
    _base_mapper = MedicalPrescriptionOrderImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['pat_id'],
                                'carepoint.medical.patient')
        self._import_dependency(record['md_id'],
                                'carepoint.medical.physician')

    #
    # def _after_import(self, partner_binding):
    #     """ Import the addresses """
    #     book = self.unit_for(PartnerAddressBook, model='carepoint.address')
    #     book.import_addresses(self.carepoint_id, partner_binding.id)


@carepoint
class MedicalPrescriptionOrderExportMapper(ExportMapper):
    _model_name = 'carepoint.medical.prescription.order'

    direct = [
        (none('date_start_treatment'), 'start_date'),
        (none('date_stop_treatment'), 'expire_date'),
        (none('qty'), 'written_qty'),
        (none('frequency'), 'freq_of_admin'),
        (none('quantity'), 'units_per_dose'),
        # Note that the col naming seems to be reversed *shrug*
        # ('refill_qty_original', 'refills_left'),
        # ('refill_qty_remain', 'refills_orig'),
    ]

    @mapping
    def pat_id(self, record):
        return {'pat_id': record.carepoint_id}


@carepoint
class MedicalPrescriptionOrderExporter(CarepointExporter):
    _model_name = ['carepoint.medical.prescription.order']
    _base_mapper = MedicalPrescriptionOrderExportMapper
