# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector_v9.unit.mapper import (mapping,
                                               only_create,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import (BaseImportMapper,
                           trim,
                           trim_and_titleize,
                           )
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class FdbForm(models.Model):
    _inherit = 'fdb.form'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.form',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointFdbForm(models.Model):
    _name = 'carepoint.fdb.form'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.form': 'odoo_id'}
    _description = 'Carepoint FdbForm'
    _cp_lib = 'fdb_form'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbForm',
        comodel_name='fdb.form',
        required=True,
        ondelete='restrict'
    )


@carepoint
class FdbFormAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.form'


@carepoint
class FdbFormBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbForms.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.form']


@carepoint
class FdbFormImportMapper(BaseImportMapper):
    _model_name = 'carepoint.fdb.form'
    direct = [
        (trim('gcdf'), 'gcdf'),
        (trim('dose'), 'code'),
        (trim('gcdf'), 'carepoint_id'),
        (trim_and_titleize('gcdf_desc'), 'name'),
        ('update_yn', 'update_yn'),
    ]

    @mapping
    @only_create
    def odoo_id(self, record):
        """ Will bind the form on a existing form with same name """
        form = self.env['medical.drug.form'].search([
            ('name', '=', record['name'].strip().title()),
        ])
        if not form:
            return
        carepoint_form = self.env['fdb.form'].search([
            ('form_id', '=', form.id),
        ])
        if carepoint_form:
            return {'odoo_id': carepoint_form[0].id}
        return {'form_id': form.id}


@carepoint
class FdbFormImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.form']
    _base_mapper = FdbFormImportMapper
