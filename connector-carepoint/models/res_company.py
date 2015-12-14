# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Dave Lasley <dave@laslabs.com>
#    Copyright: 2015 LasLabs, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from collections import namedtuple
from openerp import models, fields, api
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.backend_adapter import BackendAdapter
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  ImportMapper
                                                  )
from openerp.addons.connector.exception import IDMissingInBackend
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..connector import get_environment
from ..backend import carepoint
from ..related_action import unwrap_binding
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class CarepointResCompany(models.Model):
    """ Binding Model for the Carepoint Store """
    _name = 'carepoint.res.company'
    _inherit = 'carepoint.binding'
    _inherits = {'res.company': 'odoo_id'}
    _description = 'Carepoint Company'

    odoo_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        ondelete='cascade'
    )
    backend_id = fields.Many2one(
        comodel_name='carepoint.backend',
        related='website_id.backend_id',
        string='Carepoint Backend',
        store=True,
        readonly=True,
        # override 'carepoint.binding', can't be INSERTed if True:
        required=False,
    )

    _sql_constraints = [
        ('odoo_uniq', 'unique(backend_id, odoo_id)',
         'A Carepoint binding for this partner already exists.'),
    ]


class ResCompany(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _inherit = 'res.company'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.res.company',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class ResCompanyAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Store """
    _model_name = 'carepoint.res.company'
    _cp_lib = 'store' # Name of model in Carepoint lib (snake_case)

@carepoint
class ResCompanyBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Stores.
    For every partner in the list, a delayed job is created.
    """
    _model_name = ['carepoint.res.company']
    _cp_lib = 'store' # Name of model in Carepoint lib (snake_case)

    def run(self, filters=None):
        """ Run the synchronization """
        from_date = filters.pop('from_date', None)
        to_date = filters.pop('to_date', None)
        carepoint_website_ids = [filters.pop('carepoint_website_id')]
        record_ids = self.backend_adapter.search(
            filters,
            from_date=from_date,
            to_date=to_date,
            carepoint_website_ids=carepoint_website_ids)
        _logger.info('search for carepoint partners %s returned %s',
                     filters, record_ids)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class ResCompanyImportMapper(ImportMapper):
    _model_name = 'carepoint.res.company'
    _cp_lib = 'store' # Name of model in Carepoint lib (snake_case)

    direct = [
        ('name', 'name'),
        ('fed_tax_id', 'vat'),
        ('url', 'website'),
        ('email', 'email'),
        ('nabp', 'nabp_num'),
        ('medcaid_no', 'medicaid_num'),
        ('NPI', 'npi_num'),
        
        #   Magic cols @TODO: uids
        ('add_date', 'create_date'),
        ('chg_date', 'write_date'),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        """ Will bind the customer on a existing partner
        with the same email """
        company_id = self.env['res.company'].search(
            [('email', '=', record['email'])],
            limit=1,
        )
        if company_id:
            return {'odoo_id': company_id.id}


@carepoint
class ResCompanyImporter(CarepointImporter):
    _model_name = ['carepoint.res.company']

    _base_mapper = ResCompanyImportMapper
    
    def _create(self, data):
        binding = super(StoreImporter, self)._create(data)
        checkpoint = self.unit_for(ResCompanyAddCheckpoint)
        checkpoint.run(binding.id)
        return binding

    # 
    # def _after_import(self, partner_binding):
    #     """ Import the addresses """
    #     book = self.unit_for(PartnerAddressBook, model='carepoint.address')
    #     book.import_addresses(self.carepoint_id, partner_binding.id)


@carepoint
class ResCompanyAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.res.company record """
    _model_name = ['carepoint.res.company', ]
    _cp_lib = 'store' # Name of model in Carepoint lib (snake_case)

    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)



@job(default_channel='root.carepoint')
def company_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of companies modified on Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(ResCompanyBatchImporter)
    importer.run(filters=filters)
