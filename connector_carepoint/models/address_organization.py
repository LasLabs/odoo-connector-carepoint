# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields, api
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..backend import carepoint
from ..unit.import_synchronizer import DelayedBatchImporter

from .address_abstract import (CarepointAddressAbstractImportMapper,
                               CarepointAddressAbstractImporter,
                               CarepointAddressAbstractExportMapper,
                               CarepointAddressAbstractExporter,
                               )

_logger = logging.getLogger(__name__)


class CarepointCarepointAddressOrganization(models.Model):
    """ Binding Model for the Carepoint Address Organization """
    _name = 'carepoint.carepoint.address.organization'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.address.organization': 'odoo_id'}
    _description = 'Carepoint Address Organization Many2Many Rel'
    _cp_lib = 'pharmacy_address'

    odoo_id = fields.Many2one(
        comodel_name='carepoint.address.organization',
        string='Address',
        required=True,
        ondelete='cascade'
    )


class CarepointAddressOrganization(models.Model):
    """ Adds the ``One2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.address.organization'
    _inherit = 'carepoint.address.abstract'
    _description = 'Carepoint Address Organization'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.address.organization',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )

    @api.model
    def _default_res_model(self):
        """ It returns the res model. """
        return 'carepoint.organization'


@carepoint
class CarepointAddressOrganizationAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Address Organization """
    _model_name = 'carepoint.carepoint.address.organization'


@carepoint
class CarepointAddressOrganizationBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Address Organizations.
    For every address in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.address.organization']


@carepoint
class CarepointAddressOrganizationImportMapper(
    CarepointAddressAbstractImportMapper,
):
    _model_name = 'carepoint.carepoint.address.organization'

    @mapping
    @only_create
    def partner_id(self, record):
        """ It returns either the commercial partner or parent & defaults """
        binder = self.binder_for('carepoint.medical.organization')
        organization_id = binder.to_odoo(record['org_id'], browse=True)
        _sup = super(CarepointAddressOrganizationImportMapper, self)
        return _sup.partner_id(
            record, organization_id,
        )

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%d,%d' % (record['org_id'],
                                           record['addr_id'])}


@carepoint
class CarepointAddressOrganizationImporter(
    CarepointAddressAbstractImporter,
):
    _model_name = ['carepoint.carepoint.address.organization']
    _base_mapper = CarepointAddressOrganizationImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        super(
            CarepointAddressOrganizationImporter, self
        )._import_dependencies()
        self._import_dependency(self.carepoint_record['org_id'],
                                'carepoint.medical.organization')


@carepoint
class CarepointAddressOrganizationUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.address.organization'

    def _import_addresses(self, organization_id, partner_binding):
        adapter = self.unit_for(CarepointCRUDAdapter)
        importer = self.unit_for(CarepointAddressOrganizationImporter)
        address_ids = adapter.search(org_id=organization_id)
        for address_id in address_ids:
            importer.run(address_id)


@carepoint
class CarepointAddressOrganizationExportMapper(
    CarepointAddressAbstractExportMapper
):
    _model_name = 'carepoint.carepoint.address.organization'

    @mapping
    def org_id(self, binding):
        binder = self.binder_for('carepoint.org.bind')
        rec_id = binder.to_backend(binding.res_id)
        return {'org_id': rec_id}


@carepoint
class CarepointAddressOrganizationExporter(
    CarepointAddressAbstractExporter
):
    _model_name = 'carepoint.carepoint.address.organization'
    _base_mapper = CarepointAddressOrganizationExportMapper
