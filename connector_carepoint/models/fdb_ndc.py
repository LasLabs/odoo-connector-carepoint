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


class CarepointFdbNdc(models.Model):
    _name = 'carepoint.fdb.ndc'
    _inherit = 'carepoint.binding'
    _inherits = {'fdb.ndc': 'odoo_id'}
    _description = 'Carepoint FdbNdc'
    _cp_lib = 'fdb_ndc'  # Name of model in Carepoint lib (snake_case)

    odoo_id = fields.Many2one(
        string='FdbNdc',
        comodel_name='fdb.ndc',
        required=True,
        ondelete='restrict'
    )

class FdbNdc(models.Model):
    _inherit = 'fdb.ndc'

    carepoint_bind_ids = fields.One2many(
        comodel_name='carepoint.fdb.ndc',
        inverse_name='odoo_id',
        string='Carepoint Bindings',
    )


@carepoint
class FdbNdcAdapter(CarepointCRUDAdapter):
    _model_name = 'carepoint.fdb.ndc'


@carepoint
class FdbNdcBatchImporter(DelayedBatchImporter):
    """ Import the Carepoint FdbNdcs.
    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _model_name = ['carepoint.fdb.ndc']

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        record_ids = self.backend_adapter.search(**filters)
        for record_id in record_ids:
            self._import_record(record_id)


@carepoint
class FdbNdcImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.ndc'
    direct = [
        ('ndc', 'name'),
        ('lblrid', 'lblrid'),
        ('gcn_seqno', 'gcn_seqno'),
        ('ps', 'ps'),
        ('df', 'df'),
        ('ad', 'ad'),
        ('ln', 'ln'),
        ('bn', 'bn'),
        ('pndc', 'pndc'),
        ('repndc', 'repndc'),
        ('ndcfi', 'ndcfi'),
        ('daddnc', 'daddnc'),
        ('dupdc', 'dupdc'),
        ('desi', 'desi'),
        ('desdtec', 'desdtec'),
        ('desi2', 'desi2'),
        ('des2dtec', 'des2dtec'),
        ('dea', 'dea'),
        ('cl', 'cl'),
        ('gpi', 'gpi'),
        ('hosp', 'hosp'),
        ('innov', 'innov'),
        ('ipi', 'ipi'),
        ('mini', 'mini'),
        ('maint', 'maint'),
        ('obc', 'obc'),
        ('obsdtec', 'obsdtec'),
        ('ppi', 'ppi'),
        ('stpk', 'stpk'),
        ('repack', 'repack'),
        ('top200', 'top200'),
        ('ud', 'ud'),
        ('csp', 'csp'),
        ('color', 'color'),
        ('flavor', 'flavor'),
        ('shape', 'shape'),
        ('ndl_gdge', 'ndl_gdge'),
        ('ndl_lngth', 'ndl_lngth'),
        ('syr_cpcty', 'syr_cpcty'),
        ('shlf_pck', 'shlf_pck'),
        ('shipper', 'shipper'),
        ('skey', 'skey'),
        ('hcfa_fda', 'hcfa_fda'),
        ('hcfa_ps', 'hcfa_ps'),
        ('hcfa_appc', 'hcfa_appc'),
        ('hcfa_mrkc', 'hcfa_mrkc'),
        ('hcfa_trmc', 'hcfa_trmc'),
        ('hcfa_typ', 'hcfa_typ'),
        ('hcfa_desc1', 'hcfa_desc1'),
        ('hcfa_desi1', 'hcfa_desi1'),
        ('uu', 'uu'),
        ('pd', 'pd'),
        ('ln25', 'ln25'),
        ('ln25i', 'ln25i'),
        ('gpidc', 'gpidc'),
        ('bbdc', 'bbdc'),
        ('home', 'home'),
        ('inpcki', 'inpcki'),
        ('outpcki', 'outpcki'),
        ('obc_exp', 'obc_exp'),
        ('ps_equiv', 'ps_equiv'),
        ('plblr', 'plblr'),
        ('hcpc', 'hcpc'),
        ('top50gen', 'top50gen'),
        ('obc3', 'obc3'),
        ('gmi', 'gmi'),
        ('gni', 'gni'),
        ('gsi', 'gsi'),
        ('gti', 'gti'),
        ('ndcgi1', 'ndcgi1'),
        ('user_gcdf', 'user_gcdf'),
        ('user_str', 'user_str'),
        ('real_product_yn', 'real_product_yn'),
        ('no_update_yn', 'no_update_yn'),
        ('no_prc_update_yn', 'no_prc_update_yn'),
        ('user_product_yn', 'user_product_yn'),
        ('cpname_short', 'cpname_short'),
        ('status_cn', 'status_cn'),
        ('update_yn', 'update_yn'),
        ('active_yn', 'active_yn'),
        ('ln60', 'ln60'),
    ]

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['id']}


@carepoint
class FdbNdcImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.ndc']

    _base_mapper = FdbNdcImportMapper

    def _create(self, data):
        odoo_binding = super(FdbNdcImporter, self)._create(data)
        checkpoint = self.unit_for(FdbNdcAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding


@carepoint
class FdbNdcAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.ndc record """
    _model_name = ['carepoint.fdb.ndc']
    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint')
def fdb_ndc_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of NDCs from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbNdcBatchImporter)
    importer.run(filters=filters)

