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
from ..backend import carepoint
from ..unit.import_synchronizer import DelayedBatchImporter

from .address_abstract import (CarepointAddressAbstractImportMapper,
                               CarepointAddressAbstractImporter,
                               )

_logger = logging.getLogger(__name__)


class CarepointCarepointAddressStore(models.Model):
    """ Binding Model for the Carepoint Address Store """
    _name = 'carepoint.carepoint.address.store'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.address.store': 'odoo_id'}
    _description = 'Carepoint Address Store Many2Many Rel'
    _cp_lib = 'store_address'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='carepoint.address.store',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class CarepointAddressStore(models.Model):
    """ Adds the ``One2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.address.store'
    _inherit = 'carepoint.address.abstract'
    _description = 'Carepoint Address Store'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.address.store',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class CarepointAddressStoreAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Address Store """
    _model_name = 'carepoint.carepoint.address.store'


@carepoint
class CarepointAddressStoreBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Address Stores.
    For every address in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.address.store']


@carepoint
class CarepointAddressStoreImportMapper(
    CarepointAddressAbstractImportMapper,
):
    _model_name = 'carepoint.carepoint.address.store'

    @mapping
    @only_create
    def partner_id(self, record):
        """ It returns either the commercial partner or parent & defaults """
        binder = self.binder_for('carepoint.carepoint.store')
        store_id = binder.to_odoo(record['store_id'], browse=True)
        _sup = super(CarepointAddressStoreImportMapper, self)
        return _sup.partner_id(
            record, store_id,
        )

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%d,%d' % (record['store_id'],
                                           record['addr_id'])}


@carepoint
class CarepointAddressStoreImporter(
    CarepointAddressAbstractImporter,
):
    _model_name = ['carepoint.carepoint.address.store']
    _base_mapper = CarepointAddressStoreImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        super(CarepointAddressStoreImporter, self)._import_dependencies()
        self._import_dependency(self.carepoint_record['store_id'],
                                'carepoint.carepoint.store')


@carepoint
class CarepointAddressStoreUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.address.store'

    def _import_addresses(self, store_id, partner_binding):
        adapter = self.unit_for(CarepointCRUDAdapter)
        importer = self.unit_for(CarepointAddressStoreImporter)
        address_ids = adapter.search(store_id=store_id)
        for address_id in address_ids:
            importer.run(address_id)
