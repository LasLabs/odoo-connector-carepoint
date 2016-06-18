# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import re
from openerp import models, fields, _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  ImportMapper
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper, trim, trim_and_titleize
from ..connector import get_environment
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from ..connector import add_checkpoint
from .fdb_unit import ureg
from pint.errors import DimensionalityError, UndefinedUnitError
from psycopg2 import IntegrityError
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)


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
        (trim('ndc'), 'name'),
        (trim('lblrid'), 'lblrid'),
        ('gcn_seqno', 'gcn_seqno'),
        ('ps', 'ps'),
        ('df', 'df'),
        (trim('ad'), 'ad'),
        (trim('ln'), 'ln'),
        (trim('bn'), 'bn'),
        ('pndc', 'pndc'),
        ('repndc', 'repndc'),
        ('ndcfi', 'ndcfi'),
        ('daddnc', 'daddnc'),
        ('dupdc', 'dupdc'),
        (trim('desi'), 'desi'),
        ('desdtec', 'desdtec'),
        (trim('desi2'), 'desi2'),
        ('des2dtec', 'des2dtec'),
        ('dea', 'dea'),
        (trim('cl'), 'cl'),
        ('gpi', 'gpi'),
        ('hosp', 'hosp'),
        ('innov', 'innov'),
        ('ipi', 'ipi'),
        ('mini', 'mini'),
        ('maint', 'maint'),
        (trim('obc'), 'obc'),
        (trim('obsdtec'), 'obsdtec'),
        ('ppi', 'ppi'),
        ('stpk', 'stpk'),
        ('repack', 'repack'),
        ('top200', 'top200'),
        ('ud', 'ud'),
        ('csp', 'csp'),
        (trim('color'), 'color'),
        (trim('flavor'), 'flavor'),
        (trim('shape'), 'shape'),
        ('ndl_gdge', 'ndl_gdge'),
        ('ndl_lngth', 'ndl_lngth'),
        ('syr_cpcty', 'syr_cpcty'),
        ('shlf_pck', 'shlf_pck'),
        ('shipper', 'shipper'),
        (trim('skey'), 'skey'),
        (trim('hcfa_fda'), 'hcfa_fda'),
        (trim('hcfa_unit'), 'hcfa_unit'),
        ('hcfa_ps', 'hcfa_ps'),
        ('hcfa_appc', 'hcfa_appc'),
        ('hcfa_mrkc', 'hcfa_mrkc'),
        ('hcfa_trmc', 'hcfa_trmc'),
        ('hcfa_typ', 'hcfa_typ'),
        ('hcfa_desc1', 'hcfa_desc1'),
        ('hcfa_desi1', 'hcfa_desi1'),
        ('uu', 'uu'),
        (trim('pd'), 'pd'),
        (trim('ln25'), 'ln25'),
        ('ln25i', 'ln25i'),
        ('gpidc', 'gpidc'),
        ('bbdc', 'bbdc'),
        ('home', 'home'),
        ('inpcki', 'inpcki'),
        ('outpcki', 'outpcki'),
        (trim('obc_exp'), 'obc_exp'),
        ('ps_equiv', 'ps_equiv'),
        ('plblr', 'plblr'),
        (trim('hcpc'), 'hcpc'),
        ('top50gen', 'top50gen'),
        (trim('obc3'), 'obc3'),
        ('gmi', 'gmi'),
        ('gni', 'gni'),
        ('gsi', 'gsi'),
        ('gti', 'gti'),
        ('ndcgi1', 'ndcgi1'),
        (trim('user_gcdf'), 'user_gcdf'),
        (trim('user_str'), 'user_str'),
        ('real_product_yn', 'real_product_yn'),
        ('no_update_yn', 'no_update_yn'),
        ('no_prc_update_yn', 'no_prc_update_yn'),
        ('user_product_yn', 'user_product_yn'),
        (trim('cpname_short'), 'cpname_short'),
        (trim('status_cn'), 'status_cn'),
        ('update_yn', 'update_yn'),
        ('active_yn', 'active_yn'),
        (trim('ln60'), 'ln60'),
    ]

    @mapping
    @only_create
    def medicament_id(self, record):

        medicament_obj = self.env['medical.medicament']
        medicament_name = record['bn'].strip()
        binder = self.binder_for('carepoint.fdb.gcn')
        fdb_gcn_id = binder.to_odoo(record['gcn_seqno'], browse=True)
        binder = self.binder_for('carepoint.fdb.ndc.cs.ext')
        cs_ext_id = binder.to_odoo(record['ndc'].strip(), browse=True)
        binder = self.binder_for('carepoint.fdb.gcn.seq')
        fdb_gcn_seq_id = binder.to_odoo(record['gcn_seqno'], browse=True)

        strength_str = ''
        route_id = 0
        form_id = 0
        gpi = 0
        is_prescription = False

        if cs_ext_id:
            strength_str = cs_ext_id.dn_str.lower().strip()
            route_id = cs_ext_id.route_id.route_id
            form_id = cs_ext_id.form_id.form_id
            gpi = cs_ext_id.gpi
            is_prescription = cs_ext_id.rx_only_yn

        if not strength_str:
            strength_str = fdb_gcn_seq_id.str.lower().strip()
        if not route_id:
            route_id = fdb_gcn_seq_id.route_id.route_id
        if not form_id:
            form_id = fdb_gcn_seq_id.form_id.form_id

        strength_str = strength_str.replace('%', 'percent')

        try:
            strength_obj = ureg(strength_str)
        except DimensionalityError:
            strength_parts = strength_str.split('-')
            unit_arr = []
            uom_str = 'unit'
            strength_re = re.compile(r'(?P<unit>\d+\.?\d?)\s?(?P<uom>[a-z]?)')
            # Iter in reverse because UOM is typically last if only one
            for strength_part in reversed(strength_parts):
                if len(unit_arr):
                    unit_arr.append('/')
                match = strength_re.match(strength_part)
                if match:
                    unit_arr.append(match.group('unit'))
                    if match.group('uom'):
                        uom_str = match.group('uom')
                    if uom_str:
                        unit_arr.append(uom_str)
            strength_obj = ureg(' '.join(unit_arr))
        _logger.debug('%s, %s, %s, %s', route_id, form_id, fdb_gcn_seq_id, cs_ext_id)
        try:
            strength_str = strength_str.replace(
                '%d' % strength_obj.m, ''
            ).strip().upper()
            strength_num = float(strength_obj.m)
        except AttributeError:
            strength_str = strength_str.replace(
                '%d' % strength_obj, ''
            ).strip().upper()
            strength_num = float(strength_obj)
        strength_uom_id = self.env['product.uom'].search([
            ('name', '=', strength_str),
        ],
            limit=1,
        )

        medicament_id = medicament_obj.search([
            ('name', '=', medicament_name),
            ('drug_route_id', '=', route_id.id),
            ('drug_form_id', '=', form_id.id),
            ('strength', '=', strength_num),
            ('strength_uom_id', '=', strength_uom_id.id),
        ],
            limit=1,
        )

        if is_prescription:
            categ_id = self.env.ref('medical_prescription_sale.product_category_rx')
        else:
            categ_id = self.env.ref('medical_prescription_sale.product_category_otc')

        if not len(medicament_id):
            code = record['dea']
            if not code:
                code = '0'
            binder = self.binder_for('carepoint.fdb.ndc')
            fdb_ndc_id = binder.to_odoo(record['ndc'])
            fdb_ndc_id = self.env['fdb.ndc'].browse(fdb_ndc_id)
            hcfa_unit = record['hcfa_unit'] or ''
            sale_uom_id = self.env['product.uom'].search([
                ('name', '=', hcfa_unit.strip()),
            ],
                limit=1,
            )
            if not sale_uom_id:
                sale_uom_id = self.env['product.uom'].search([
                    ('name', '=', 'UNIT'),
                ],
                    limit=1,
                )

            medicament_vals = {
                'name': medicament_name,
                'drug_route_id': route_id.id,
                'drug_form_id': form_id.id,
                'gpi': str(gpi),
                'control_code': code,
                'categ_id': categ_id.id,
                'strength': strength_num,
                'strength_uom_id': strength_uom_id.id,
                'uom_id': sale_uom_id.id,
                'uom_po_id': sale_uom_id.id,
                'gcn_id': fdb_gcn_id.gcn_id.id,
                'type': 'product',
                'property_account_income_id':
                    self.backend_record.default_product_income_account_id.id,
                'property_account_expense_id':
                    self.backend_record.default_product_expense_account_id.id,
                'categ_id': self.backend_record.default_category_id.id,
                'website_published': True,
            }
            try:
                medicament_id = medicament_obj.create(medicament_vals)
            except IntegrityError, e:
                raise ValidationError(_(
                    'Unable to create medicament w/ vals: %s '
                    '--- Original Error: %s'
                ) % (medicament_vals, e))

        return {'medicament_id': medicament_id.id}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['ndc'].strip()}


@carepoint
class FdbNdcImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.ndc']

    _base_mapper = FdbNdcImportMapper

    def _create(self, data):
        odoo_binding = super(FdbNdcImporter, self)._create(data)
        checkpoint = self.unit_for(FdbNdcAddCheckpoint)
        checkpoint.run(odoo_binding.id)
        return odoo_binding

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        try:
            self._import_dependency(record['ndc'],
                                    'carepoint.fdb.ndc.cs.ext')
        except IndexError:
            # Won't exist in cs_ext if user_product_yn == 0
            pass
        self._import_dependency(record['gcn_seqno'],
                                'carepoint.fdb.gcn')


@carepoint
class FdbNdcAddCheckpoint(ConnectorUnit):
    """ Add a connector.checkpoint on the carepoint.fdb.ndc record """
    _model_name = ['carepoint.fdb.ndc']
    def run(self, binding_id):
        add_checkpoint(self.session,
                       self.model._name,
                       binding_id,
                       self.backend_record.id)


@job(default_channel='root.carepoint.fdb')
def fdb_ndc_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of NDCs from Carepoint """
    if filters is None:
        filters = {}
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(FdbNdcBatchImporter)
    importer.run(filters=filters)
