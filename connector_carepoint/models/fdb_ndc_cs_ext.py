# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from odoo.addons.connector_v9.unit.mapper import (mapping,
                                               only_create,
                                               )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import BaseImportMapper, trim
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )

_logger = logging.getLogger(__name__)


class FdbNdcCsExt(models.Model):
    _inherit = 'fdb.ndc.cs.ext'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.ndc.cs.ext',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


class CarepointFdbNdcCsExt(models.Model):
    _name = 'carepoint.fdb.ndc.cs.ext'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.ndc.cs.ext': 'odoo_id'}
    _description = 'Carepoint FdbNdcCsExt'
    _cp_lib = 'fdb_ndc_cs_ext'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbNdcCsExt',
        comodel_name='fdb.ndc.cs.ext',
        required=True,
        ondelete='restrict'
    )


@carepoint
class FdbNdcCsExtAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.ndc.cs.ext'


@carepoint
class FdbNdcCsExtBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbNdcCsExts.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.ndc.cs.ext']


@carepoint
class FdbNdcCsExtImportMapper(BaseImportMapper):
    _model_name = 'carepoint.fdb.ndc.cs.ext'
    direct = [
        (trim('ndc'), 'ndc'),
        (trim('short_name'), 'short_name'),
        (trim('lot_no'), 'lot_no'),
        (trim('orig_mfg'), 'orig_mfg'),
        ('pref_gen_yn', 'pref_gen_yn'),
        ('active_yn', 'active_yn'),
        ('drug_expire_days', 'drug_expire_days'),
        ('formulary_yn', 'formulary_yn'),
        ('compound_yn', 'compound_yn'),
        ('sup_upd_gen_yn', 'sup_upd_gen_yn'),
        ('sup_upd_phys_yn', 'sup_upd_phys_yn'),
        ('sup_upd_clin_yn', 'sup_upd_clin_yn'),
        ('sup_upd_fin_yn', 'sup_upd_fin_yn'),
        ('sup_upd_med_yn', 'sup_upd_med_yn'),
        (trim('dn_str'), 'dn_str'),
        ('rx_only_yn', 'rx_only_yn'),
        ('manual_yn', 'manual_yn'),
        (trim('brand_ndc'), 'brand_ndc'),
        ('add_user_id', 'add_user_id'),
        ('add_date', 'add_date'),
        ('chg_user_id', 'chg_user_id'),
        ('app_flags', 'app_flags'),
        ('timestmp', 'timestmp'),
        ('comp_yn', 'comp_yn'),
        (trim('dea'), 'dea'),
        ('dea_chg_user', 'dea_chg_user'),
        ('dea_chg_date', 'dea_chg_date'),
        (trim('ln'), 'ln'),
        ('ln_chg_user', 'ln_chg_user'),
        ('ln_chg_date', 'ln_chg_date'),
        ('fdb_chg_date', 'fdb_chg_date'),
        ('ud_svc_code', 'ud_svc_code'),
        ('gpi', 'gpi'),
        ('gpi_chg_user', 'gpi_chg_user'),
        ('gpi_chg_date', 'gpi_chg_date'),
        ('bill_increment', 'bill_increment'),
        ('formula_id', 'formula_id'),
        (trim('alt_iptside1'), 'alt_iptside1'),
        (trim('alt_iptside2'), 'alt_iptside2'),
        (trim('dose_multiplier'), 'dose_multiplier'),
        (trim('default_daw_override'), 'default_daw_override'),
        ('manual_price_yn', 'manual_price_yn'),
        ('compound_type_cn', 'compound_type_cn'),
        ('refrig_cn', 'refrig_cn'),
    ]

    @mapping
    def form_id(self, record):
        try:
            form_str = record['dn_form'].strip()
        except AttributeError as e:
            _logger.debug(e)
            return
        form_id = self.env['fdb.form'].search(['|',
                                               ('code', '=', form_str),
                                               ('name', '=', form_str.title()),
                                               ],
                                              limit=1,
                                              )
        return {'form_id': form_id.id}

    @mapping
    def route_id(self, record):
        if not record['dn_route']:
            record['dn_route'] = 'AP'
        route_id = self.env['fdb.route'].search([
            '|',
            ('name', '=', record['dn_route'].strip().title()),
            ('code', '=', record['dn_route'].strip()),
        ],
            limit=1,
        )
        return {'route_id': route_id.id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['ndc'].strip()}


@carepoint
class FdbNdcCsExtImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.ndc.cs.ext']
    _base_mapper = FdbNdcCsExtImportMapper

    def _get_carepoint_data(self):
        """ Return the raw Carepoint data for ``self.carepoint_id`` """
        self.carepoint_id = '%011d' % int(self.carepoint_id)
        return super(FdbNdcCsExtImporter, self)._get_carepoint_data()
