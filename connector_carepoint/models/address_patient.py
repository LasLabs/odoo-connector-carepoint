# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.connector import ConnectorUnit
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


class CarepointCarepointAddressPatient(models.Model):
    """ Binding Model for the Carepoint Address Patient """
    _name = 'carepoint.carepoint.address.patient'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.address.patient': 'odoo_id'}
    _description = 'Carepoint Address Patient Many2Many Rel'
    _cp_lib = 'patient_address'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='carepoint.address.patient',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class CarepointAddressPatient(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherits = {'carepoint.address': 'address_id'}
    _name = 'carepoint.address.patient'
    _description = 'Carepoint Address Patient'

    address_id = fields.Many2one(
        string='Address',
        comodel_name='carepoint.address',
        required=True,
        ondelete='cascade',
    )
    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.address.patient',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class CarepointAddressPatientAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Address Patient """
    _model_name = 'carepoint.carepoint.address.patient'


@carepoint
class CarepointAddressPatientBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Address Patients.
    For every address in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.address.patient']


@carepoint
class CarepointAddressPatientImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.carepoint.address.patient'

    @mapping
    @only_create
    def parent_id(self, record):
        binder = self.binder_for('carepoint.medical.patient')
        patient_id = binder.to_odoo(record['pat_id'])
        self.env['medical.patient'].browse(patient_id).partner_id
        # if not partner_id.street:
        #
        # return {
        #     'parent_id': partner_id.id,
        # }

    @mapping
    @only_create
    def partner_and_address_id(self, record):
        binder = self.binder_for('carepoint.carepoint.address')
        address_id = binder.to_odoo(record['addr_id'])
        vals = {'address_id': address_id}
        # address_id = self.env['carepoint.address'].browse(address_id)
        return vals

    @mapping
    def type(self, record):
        return {'type': 'delivery'}

    @mapping
    def customer(self, record):
        return {'customer': True}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%d,%d' % (record['pat_id'],
                                           record['addr_id'])}


@carepoint
class CarepointAddressPatientImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.address.patient']
    _base_mapper = CarepointAddressPatientImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        self._import_dependency(record['addr_id'],
                                'carepoint.carepoint.address')
        self._import_dependency(record['pat_id'],
                                'carepoint.medical.patient')


@carepoint
class CarepointAddressPatientUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.address.patient'

    def _import_addresses(self, patient_id, binding_id):
        adapter = self.unit_for(CarepointCRUDAdapter)
        importer = self.unit_for(CarepointAddressPatientImporter)
        address_ids = adapter.search(pat_id=patient_id)
        for address_id in address_ids:
            importer.run(address_id)
