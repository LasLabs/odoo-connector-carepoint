# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  ImportMapper
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper, trim
from ..connector import get_environment
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in xrange(0, len(items), length):
        yield items[index:index + length]


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

class FdbNdcCsExt(models.Model):
    _inherit = 'fdb.ndc.cs.ext'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.ndc.cs.ext',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
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

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbNdcCsExtImportMapper(CarepointImportMapper):
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
    # @only_create
    def form_id(self, record):
        form_id = self.env['medical.drug.form'].search([
            ('code', '=', record['dn_form'].strip()),
        ],
            limit=1,
        )
        return {'form_id': form_id.id}

    @mapping
    # @only_create
    def route_id(self, record):
        route_id = self.env['medical.drug.route'].search([
            ('name', '=', record['dn_route'].title()),
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

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        # @TODO: Don't assume route & form; data vs PK issue
        # self._import_dependency(record['dn_form'].strip(),
        #                         'carepoint.fdb.form')
        # self._import_dependency(record['dn_route'].strip(),
        #                         'carepoint.fdb.route')

    def _create(self, data):
        odoo_binding = super(FdbNdcCsExtImporter, self)._create(data)
        checkpoint = self.unit_for(FdbNdcCsExtAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class FdbNdcCsExtAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.ndc.cs.ext record """
    _model_name = ['carepoint.fdb.ndc.cs.ext']
    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.fdb')
def fdb_gcn_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of NDCs from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbNdcCsExtBatchImporter)
    importer.run(filters=filters)
