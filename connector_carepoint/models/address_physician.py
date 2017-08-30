# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api
from odoo.addons.connector.connector import ConnectorUnit
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               )
from ..unit.backend_adapter import CarepointAdapter
from ..unit.import_synchronizer import DelayedBatchImporter

from .address_abstract import (CarepointAddressAbstractImportMapper,
                               CarepointAddressAbstractImporter,
                               CarepointAddressAbstractExportMapper,
                               CarepointAddressAbstractExporter,
                               )

_logger = logging.getLogger(__name__)


class CarepointAddressPhysician(models.Model):
    """ Adds the ``One2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.address.physician'
    _inherit = 'carepoint.address.abstract'
    _description = 'Carepoint Address Physician'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.address.physician',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )

    @api.model
    def _default_res_model(self):
        """ It returns the res model. """
        return 'medical.physician'


class CarepointCarepointAddressPhysician(models.Model):
    """ Binding Model for the Carepoint Address Physician """
    _name = 'carepoint.carepoint.address.physician'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.address.physician': 'odoo_id'}
    _description = 'Carepoint Address Physician Many2Many Rel'
    _cp_lib = 'doctor_address'

    odoo_id = fields.Many2one(
        comodel_name='carepoint.address.physician',
        string='Address',
        required=True,
        ondelete='cascade'
    )


class CarepointAddressPhysicianAdapter(CarepointAdapter):
    """ Backend Adapter for the Carepoint Address Physician """
    _model_name = 'carepoint.carepoint.address.physician'


class CarepointAddressPhysicianBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Address Physicians.
    For every address in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.address.physician']


class CarepointAddressPhysicianImportMapper(
    CarepointAddressAbstractImportMapper,
):
    _model_name = 'carepoint.carepoint.address.physician'

    @mapping
    @only_create
    def partner_id(self, record):
        """ It returns either the commercial partner or parent & defaults """
        binder = self.binder_for('carepoint.medical.physician')
        physician = binder.to_odoo(record['md_id'], browse=True)
        _sup = super(CarepointAddressPhysicianImportMapper, self)
        return _sup.partner_id(
            record, physician,
        )

    @mapping
    @only_create
    def res_model_and_id(self, record):
        binder = self.binder_for('carepoint.medical.physician')
        physician = binder.to_odoo(record['md_id'], browse=True)
        _sup = super(CarepointAddressPhysicianImportMapper, self)
        return _sup.res_model_and_id(
            record, physician,
        )

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%d,%d' % (record['md_id'],
                                           record['addr_id'])}


class CarepointAddressPhysicianImporter(
    CarepointAddressAbstractImporter,
):
    _model_name = ['carepoint.carepoint.address.physician']
    _base_mapper = CarepointAddressPhysicianImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        super(CarepointAddressPhysicianImporter, self)._import_dependencies()
        self._import_dependency(self.carepoint_record['md_id'],
                                'carepoint.medical.physician')


class CarepointAddressPhysicianUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.address.physician'

    def _import_addresses(self, physician_id, partner_binding):
        adapter = self.unit_for(CarepointAdapter)
        importer = self.unit_for(CarepointAddressPhysicianImporter)
        address_ids = adapter.search(md_id=physician_id)
        for address_id in address_ids:
            importer.run(address_id)


class CarepointAddressPhysicianExportMapper(
    CarepointAddressAbstractExportMapper
):
    _model_name = 'carepoint.carepoint.address.physician'

    @mapping
    def md_id(self, binding):
        binder = self.binder_for('carepoint.medical.physician')
        rec_id = binder.to_backend(binding.res_id)
        return {'md_id': rec_id}


class CarepointAddressPhysicianExporter(
    CarepointAddressAbstractExporter
):
    _model_name = 'carepoint.carepoint.address.physician'
    _base_mapper = CarepointAddressPhysicianExportMapper
