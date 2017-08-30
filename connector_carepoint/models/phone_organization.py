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

from .phone_abstract import (CarepointPhoneAbstractImportMapper,
                             CarepointPhoneAbstractImporter,
                             CarepointPhoneAbstractExportMapper,
                             CarepointPhoneAbstractExporter,
                             )

_logger = logging.getLogger(__name__)


class CarepointPhoneOrganization(models.Model):
    """ Adds the ``One2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.phone.organization'
    _inherit = 'carepoint.phone.abstract'
    _description = 'Carepoint Phone Organization'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.phone.organization',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )

    @api.model
    def _default_res_model(self):
        """ It returns the res model. """
        return 'carepoint.organization'


class CarepointCarepointPhoneOrganization(models.Model):
    """ Binding Model for the Carepoint Phone Organization """
    _name = 'carepoint.carepoint.phone.organization'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.phone.organization': 'odoo_id'}
    _description = 'Carepoint Phone Organization Many2Many Rel'
    _cp_lib = 'pharmacy_phone'

    odoo_id = fields.Many2one(
        comodel_name='carepoint.phone.organization',
        string='Phone',
        required=True,
        ondelete='cascade'
    )


class CarepointPhoneOrganizationAdapter(CarepointAdapter):
    """ Backend Adapter for the Carepoint Phone Organization """
    _model_name = 'carepoint.carepoint.phone.organization'


class CarepointPhoneOrganizationBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Phone Organizations.
    For every phone in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.phone.organization']


class CarepointPhoneOrganizationImportMapper(
    CarepointPhoneAbstractImportMapper,
):
    _model_name = 'carepoint.carepoint.phone.organization'

    @mapping
    @only_create
    def partner_id(self, record):
        """ It returns either the commercial partner or parent & defaults """
        binder = self.binder_for('carepoint.medical.organization')
        organization_id = binder.to_odoo(record['org_id'], browse=True)
        _sup = super(CarepointPhoneOrganizationImportMapper, self)
        return _sup.partner_id(
            record, organization_id,
        )

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%d,%d' % (record['org_id'],
                                           record['phone_id'])}


class CarepointPhoneOrganizationImporter(
    CarepointPhoneAbstractImporter,
):
    _model_name = ['carepoint.carepoint.phone.organization']
    _base_mapper = CarepointPhoneOrganizationImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        super(
            CarepointPhoneOrganizationImporter, self
        )._import_dependencies()
        self._import_dependency(self.carepoint_record['org_id'],
                                'carepoint.medical.organization')


class CarepointPhoneOrganizationUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.phone.organization'

    def _import_phones(self, organization_id, partner_binding):
        adapter = self.unit_for(CarepointAdapter)
        importer = self.unit_for(CarepointPhoneOrganizationImporter)
        phone_ids = adapter.search(org_id=organization_id)
        for phone_id in phone_ids:
            importer.run(phone_id)


class CarepointPhoneOrganizationExportMapper(
    CarepointPhoneAbstractExportMapper
):
    _model_name = 'carepoint.carepoint.phone.organization'

    @mapping
    def org_id(self, binding):
        binder = self.binder_for('carepoint.carepoint.organization')
        rec_id = binder.to_backend(binding.res_id)
        return {'org_id': rec_id}


class CarepointPhoneOrganizationExporter(
    CarepointPhoneAbstractExporter
):
    _model_name = 'carepoint.carepoint.phone.organization'
    _base_mapper = CarepointPhoneOrganizationExportMapper
