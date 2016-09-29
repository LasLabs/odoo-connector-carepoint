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

from .phone_abstract import (CarepointPhoneAbstractImportMapper,
                             CarepointPhoneAbstractImporter,
                             )

_logger = logging.getLogger(__name__)


class CarepointCarepointPhoneStore(models.Model):
    """ Binding Model for the Carepoint Phone Store """
    _name = 'carepoint.carepoint.phone.store'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.phone.store': 'odoo_id'}
    _description = 'Carepoint Phone Store Many2Many Rel'
    _cp_lib = 'store_phone'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='carepoint.phone.store',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class CarepointPhoneStore(models.Model):
    """ Adds the ``One2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.phone.store'
    _inherit = 'carepoint.phone.abstract'
    _description = 'Carepoint Phone Store'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.phone.store',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class CarepointPhoneStoreAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Phone Store """
    _model_name = 'carepoint.carepoint.phone.store'


@carepoint
class CarepointPhoneStoreBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Phone Stores.
    For every phone in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.phone.store']


@carepoint
class CarepointPhoneStoreImportMapper(
    CarepointPhoneAbstractImportMapper,
):
    _model_name = 'carepoint.carepoint.phone.store'

    @mapping
    @only_create
    def partner_id(self, record):
        """ It returns either the commercial partner or parent & defaults """
        binder = self.binder_for('carepoint.carepoint.store')
        store_id = binder.to_odoo(record['store_id'], browse=True)
        _sup = super(CarepointPhoneStoreImportMapper, self)
        return _sup.partner_id(
            record, store_id,
        )

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': '%d,%d' % (record['store_id'],
                                           record['phone_id'])}


@carepoint
class CarepointPhoneStoreImporter(
    CarepointPhoneAbstractImporter,
):
    _model_name = ['carepoint.carepoint.phone.store']
    _base_mapper = CarepointPhoneStoreImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        super(CarepointPhoneStoreImporter, self)._import_dependencies()
        self._import_dependency(self.carepoint_record['store_id'],
                                'carepoint.carepoint.store')


@carepoint
class CarepointPhoneStoreUnit(ConnectorUnit):
    _model_name = 'carepoint.carepoint.phone.store'

    def _import_phones(self, store_id, partner_binding):
        adapter = self.unit_for(CarepointCRUDAdapter)
        importer = self.unit_for(CarepointPhoneStoreImporter)
        phone_ids = adapter.search(store_id=store_id)
        for phone_id in phone_ids:
            importer.run(phone_id)
