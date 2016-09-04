# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..backend import carepoint
from ..unit.mapper import PartnerImportMapper, trim
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


try:
    from carepoint.models.state import EnumOrderState
except ImportError:
    _logger.warning('Carepoint library is not installed')


class CarepointCarepointOrderStatus(models.Model):
    """ Binding Model for the Carepoint Store """
    _name = 'carepoint.carepoint.order.status'
    _inherit = 'carepoint.binding'
    _inherits = {'carepoint.order.status': 'odoo_id'}
    _description = 'Carepoint Pharmacy (Store)'
    _cp_lib = 'store'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        comodel_name='carepoint.order.status',
        string='Company',
        required=True,
        ondelete='cascade'
    )


class CarepointOrderStatus(models.Model):
    """ Adds the ``one2many`` relation to the Carepoint bindings
    (``carepoint_bind_ids``)
    """
    _name = 'carepoint.order.status'
    _description = 'Carepoint Order Status'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.carepoint.order.status',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )
    state = fields.Selection(
        lambda _: [(s.value, s.name) for s in EnumOrderState],
        required=True,
        default=EnumOrderState.entered.value,
    )
    name = fields.Char(
        required=True,
    )
    workflow_id = fields.Many2one(
        string='Related Workflow',
        comodel_name='workflow',
        required=True,
    )


@carepoint
class CarepointOrderStatusAdapter(CarepointCRUDAdapter):
    """ Backend Adapter for the Carepoint Store """
    _model_name = 'carepoint.carepoint.order.status'


@carepoint
class CarepointOrderStatusBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint Stores.
    For every company in the list, a delayed job is created.
    """
    _model_name = ['carepoint.carepoint.order.status']


@carepoint
class CarepointOrderStatusImportMapper(PartnerImportMapper):
    _model_name = 'carepoint.carepoint.order.status'

    direct = [
        (trim('descr'), 'name'),
        ('state_cn', 'state'),
        ('OmStatus', 'carepoint_id'),
    ]


@carepoint
class CarepointOrderStatusImporter(CarepointImporter):
    _model_name = ['carepoint.carepoint.order.status']
    _base_mapper = CarepointOrderStatusImportMapper
