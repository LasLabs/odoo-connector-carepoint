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


class CarepointMedicalPrescriptionOrder(models.Model):
    """ Binding Model for the Carepoint Prescription """
    _name = 'carepoint.medical.prescription.order'
    _inherit = 'carepoint.binding'
    _inherits = {'medical.prescription.order': 'odoo_id'}
    _description = 'Carepoint Prescription'
    _cp_lib = 'prescription'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='medical.prescription.order',
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

    # Pass-thru first Rx Line to Rx
    # @TODO: Better solution
    medicament_name = fields.Char(
        help='Medicament name in CarePoint (includes strength, etc.)',
        compute=lambda s: s._compute_rx_line_properties(),
        inverse=lambda s: s._set_rx_line_properties(),
    )
    medicament_ndc = fields.Char(
        compute=lambda s: s._compute_rx_line_properties(),
        inverse=lambda s: s._set_rx_line_properties(),
    )
    date_start_treatment = fields.Datetime(
        compute=lambda s: s._compute_rx_line_properties(),
        inverse=lambda s: s._set_rx_line_properties(),
    )
    date_stop_treatment = fields.Datetime(
        compute=lambda s: s._compute_rx_line_properties(),
        inverse=lambda s: s._set_rx_line_properties(),
    )
    refill_qty_original = fields.Float(
        compute=lambda s: s._compute_rx_line_properties(),
        inverse=lambda s: s._set_rx_line_properties(),
    )
    refill_qty_remain = fields.Float(
        compute=lambda s: s._compute_rx_line_properties(),
        inverse=lambda s: s._set_rx_line_properties(),
    )

    _sql_constraints = [
        ('odoo_uniq', 'unique(backend_id, odoo_id)',
         'A Carepoint binding for this prescription already exists.'),
    ]

    @api.multi
    def _compute_rx_line_properties(self):
        for rec_id in self:
            if not len(rec_id.prescription_order_line_ids):
                continue
            rx_line_id = rec_id.prescription_order_line_ids[0]
            rec_id.date_start_treatment = rx_line_id.date_start_treatment
            rec_id.date_stop_treatment = rx_line_id.date_stop_treatment
            rec_id.refill_qty_original = rx_line_id.refill_qty_original
            rec_id.refill_qty_remain = rx_line_id.refill_qty_remain
            rec_id.medicament_name = rx_line_id.medicament_id.display_name

    @api.multi
    def _set_rx_line_properties(self):
        for rec_id in self:
            ndc_id = self.env['medical.medicament.ndc'].search([
                ('name', '=', rec_id.medicament_ndc),
            ],
                limit=1
            )
            if not len(ndc_id):
                raise ValidationError(
                    'Could not find NDC %s in database.' % (
                        rec_id.medicament_ndc
                    )
                )
            vals = {
                'patient_id': rec_id.patient_id.id,
                'date_start_treatment': rec_id.date_start_treatment,
                'date_stop_treatment': rec_id.date_stop_treatment,
                'refill_qty_original': rec_id.refill_qty_original,
                'refill_qty_remain': rec_id.refill_qty_remain,
                'medicament_id': ndc_id.medicament_id.id,
            }
            if not len(rec_id.prescription_order_line_ids):
                write_vals = [(0, 0, vals)]
            else:
                rx_line_id = rec_id.prescription_order_line_ids[0]
                write_vals = [(1, rx_line_id.id, vals)]
            rec_id.write({
                'prescription_order_line_ids': write_vals,
            })


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

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class MedicalPrescriptionOrderImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.medical.prescription.order'

    direct = [
        ('script_no', 'name'),
        ('ndc', 'medicament_ndc'),
    ]

    @mapping
    def rx_line(self, record):
        """ Perform mappings for computed fields """
        return {
            'date_start_treatment': record['start_date'],
            'date_stop_treatment': record['expire_date'],
            'qty': record['written_qty'],
            'refill_qty_remain': record['refills_left'],
            'refill_qty_original': record['refills_orig'],
        }

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['rx_id']}

    @mapping
    def physician_id(self, record):
        binder = self.binder_for('carepoint.medical.physician')
        physician_id = binder.to_odoo(record['md_id'])
        return {'physician_id': physician_id}

    @mapping
    def patient_id(self, record):
        binder = self.binder_for('carepoint.medical.patient')
        patient_id = binder.to_odoo(record['pat_id'])
        return {'patient_id': patient_id}

    @mapping
    def pharmacy_id(self, record):
        binder = self.binder_for('carepoint.medical.pharmacy')
        pharmacy_id = binder.to_odoo(record['store_id'])
        return {'pharmacy_id': pharmacy_id}


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

    def _create(self, data):
        binding = super(MedicalPrescriptionOrderImporter, self)._create(data)
        checkpoint = self.unit_for(MedicalPrescriptionOrderAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    #
    # def _after_import(self, partner_binding):
    #     """ Import the addresses """
    #     book = self.unit_for(PartnerAddressBook, model='carepoint.address')
    #     book.import_addresses(self.carepoint_id, partner_binding.id)


@carepoint
class MedicalPrescriptionOrderAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.medical.prescription.order record """
    _model_name = ['carepoint.medical.prescription.order', ]

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
    importer = env.get_connector_unit(MedicalPrescriptionOrderBatchImporter)
    importer.run(filters=filters)
