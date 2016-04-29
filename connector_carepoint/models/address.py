# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  changed_by,
                                                  only_create,
                                                  ExportMapper
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper, trim, trim_and_titleize
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


class CarepointCarepointAddress(models.Model):
    """ Binding Model for the Carepoint Address """
    _name = 'carepoint.carepoint.address'  # This is going to be confusing...
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.address': 'odoo_id'}
    _description = 'Carepoint Address'
    _cp_lib = 'address'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='carepoint.address',
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

    _sql_constraints = [
        ('odoo_uniq', 'unique(backend_id, odoo_id)',
         'A Carepoint binding for this address already exists.'),
    ]


class CarepointAddress(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherits = {'res.partner': 'partner_id'}
    _name = 'carepoint.address'
    _description = 'Carepoint Address'

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        required=True,
        ondelete='cascade',
    )
    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.address',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class CarepointAddressAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Address """
    _model_name = 'carepoint.carepoint.address'


@carepoint
class CarepointAddressBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Addresss.
    For every address in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.address']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class CarepointAddressImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.carepoint.address'

    direct = [
        (trim_and_titleize('addr1'), 'street'),
        (trim_and_titleize('addr2'), 'street2'),
        (trim_and_titleize('city'), 'city'),
    ]

    @mapping
    def type(self, record):
        return {'type': 'delivery'}

    @mapping
    def customer(self, record):
        return {'customer': False}

    @mapping
    def zip(self, record):
        zip_plus4 = record['zip_plus4'].strip()
        _zip = record['zip'].strip()
        if zip_plus4:
            _zip = '%s-%s' % (_zip, zip_plus4)
        return {'zip': _zip}

    @mapping
    def state_id(self, record):
        state_id = self.env['res.country.state'].search([
            ('code', '=', record['state_cd'].strip()),
        ],
            limit=1
        )
        return {
            'state_id': state_id.id,
            'country_id': state_id.country_id.id,
        }

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['addr_id']}


@carepoint
class CarepointAddressImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.address']

    _base_mapper = CarepointAddressImportMapper

    def _create(self, data):
        binding = super(CarepointAddressImporter, self)._create(data)
        checkpoint = self.unit_for(CarepointAddressAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    #
    # def _after_import(self, partner_binding):
    #     """ Import the addresses """
    #     book = self.unit_for(PartnerAddressBook, model='carepoint.address')
    #     book.import_addresses(self.carepoint_id, partner_binding.id)


@carepoint
class CarepointAddressExportMapper(ExportMapper):
    _model_name = 'carepoint.carepoint.address'

    direct = [
        ('street', 'addr1'),
        ('email', 'addr2'),
        ('city', 'city'),
    ]

    @mapping
    def addr_id(self, record):
        return {'addr_id': record.carepoint_id}


@carepoint
class CarepointAddressExporter(CarepointExporter):
    _model_name = ['carepoint.carepoint.address']
    _base_mapper = CarepointAddressExportMapper


@carepoint
class CarepointAddressDeleteSynchronizer(CarepointDeleter):
    _model_name = ['carepoint.carepoint.address']


@carepoint
class CarepointAddressAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.address record """
    _model_name = ['carepoint.carepoint.address', ]

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.core')
def carepoint_address_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of addresss modified on Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(CarepointAddressBatchImporter)
    importer.run(filters=filters)
