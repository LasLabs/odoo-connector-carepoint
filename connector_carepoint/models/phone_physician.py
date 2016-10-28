# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api
from odoo.addons.connector.connector import ConnectorUnit
from odoo.addons.connector.unit.mapper import (mapping,
                                               only_create,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..backend import carepoint
from ..unit.import_synchronizer import DelayedBatchImporter

from .phone_abstract import (CarepointPhoneAbstractImportMapper,
                             CarepointPhoneAbstractImporter,
                             CarepointPhoneAbstractExportMapper,
                             CarepointPhoneAbstractExporter,
                             )

_logger = logging.getLogger(__name__)


class CarepointPhonePhysician(models.Model):
    """ Adds the ``One2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.phone.physician'
    _inherit = 'carepoint.phone.abstract'
    _description = 'Carepoint Phone Physician'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.phone.physician',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )

    @api.model
    def _default_res_model(self):
        """ It returns the res model. """
        return 'medical.physician'


class CarepointCarepointPhonePhysician(models.Model):
    """ Binding Model for the Carepoint Phone Physician """
    _name = 'carepoint.carepoint.phone.physician'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.phone.physician': 'odoo_id'}
    _description = 'Carepoint Phone Physician Many2Many Rel'
    _cp_lib = 'doctor_phone'

    odoo_id = fields.Many2one(
        comodel_name='carepoint.phone.physician',
        string='Phone',
        required=True,
        ondelete='cascade'
    )


@carepoint
class CarepointPhonePhysicianAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Phone Physician """
    _model_name = 'carepoint.carepoint.phone.physician'


@carepoint
class CarepointPhonePhysicianBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Phone Physicians.
    For every phone in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.phone.physician']


@carepoint
class CarepointPhonePhysicianImportMapper(
    CarepointPhoneAbstractImportMapper,
):
    _model_name = 'carepoint.carepoint.phone.physician'

    @mapping
    @only_create
    def partner_id(self, record):
        """ It returns either the commercial partner or parent & defaults """
        binder = self.binder_for('carepoint.medical.physician')
        physician = binder.to_odoo(record['md_id'], browse=True)
        _sup = super(CarepointPhonePhysicianImportMapper, self)
        return _sup.partner_id(
            record, physician,
        )

    @mapping
    @only_create
    def res_model_and_id(self, record):
        binder = self.binder_for('carepoint.medical.physician')
        physician = binder.to_odoo(record['md_id'], browse=True)
        _sup = super(CarepointPhonePhysicianImportMapper, self)
        return _sup.res_model_and_id(
            record, physician,
        )

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%d,%d' % (record['md_id'],
                                           record['phone_id'])}


@carepoint
class CarepointPhonePhysicianImporter(
    CarepointPhoneAbstractImporter,
):
    _model_name = ['carepoint.carepoint.phone.physician']
    _base_mapper = CarepointPhonePhysicianImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        super(CarepointPhonePhysicianImporter, self)._import_dependencies()
        self._import_dependency(self.carepoint_record['md_id'],
                                'carepoint.medical.physician')


@carepoint
class CarepointPhonePhysicianUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.phone.physician'

    def _import_phones(self, physician_id, partner_binding):
        adapter = self.unit_for(CarepointCRUDAdapter)
        importer = self.unit_for(CarepointPhonePhysicianImporter)
        phone_ids = adapter.search(md_id=physician_id)
        for phone_id in phone_ids:
            importer.run(phone_id)


@carepoint
class CarepointPhonePhysicianExportMapper(
    CarepointPhoneAbstractExportMapper
):
    _model_name = 'carepoint.carepoint.phone.physician'

    @mapping
    def md_id(self, binding):
        binder = self.binder_for('carepoint.medical.physician')
        rec_id = binder.to_backend(binding.res_id)
        return {'md_id': rec_id}


@carepoint
class CarepointPhonePhysicianExporter(
    CarepointPhoneAbstractExporter
):
    _model_name = 'carepoint.carepoint.phone.physician'
    _base_mapper = CarepointPhonePhysicianExportMapper
