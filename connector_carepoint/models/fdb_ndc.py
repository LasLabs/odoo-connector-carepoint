# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import re
from openerp import models, fields, _
from openerp.addons.connector.unit.mapper import (mapping,
                                                  )
from ..unit.backend_adapter import CarepointCRUDAdapter
from ..unit.mapper import CarepointImportMapper
from ..unit.mapper import trim
from ..backend import carepoint
from ..unit.import_synchronizer import (DelayedBatchImporter,
                                        CarepointImporter,
                                        )
from .fdb_unit import ureg
from psycopg2 import IntegrityError
from openerp.exceptions import ValidationError

from .fdb_img_id import FdbImgIdUnit


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


@carepoint
class FdbNdcImportMapper(CarepointImportMapper):
    _model_name = 'carepoint.fdb.ndc'

    DEFAULT_UNIT = 'unit'

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

    def _get_uom_parts(self, uom_str):
        """ @TODO: Handling for multiple UOMs (compounds)
        :returns: tuple (int:unit_num, str:uom_str)
        """

        unit_arr = []
        uom_str = uom_str.replace('%', 'percent')
        strength_re = re.compile(r'(?P<unit>\d+\.?\d*)\s?(?P<uom>[a-z]*)')
        strength_parts = uom_str.split('-')

        # Iter in reverse because UOM is typically last if only one
        for strength_part in reversed(strength_parts):
            match = strength_re.match(strength_part)
            if match:
                if len(unit_arr):
                    unit_arr.append('/')
                unit_arr.append(match.group('unit'))
                uom_str = match.group('uom') or self.DEFAULT_UNIT
                if uom_str:
                    unit_arr.append(uom_str)

        strength_obj = ureg(' '.join(unit_arr) or self.DEFAULT_UNIT)

        uom_str = uom_str.replace(str(strength_obj.m), '').strip().upper()
        unit_num = float(strength_obj.m)

        return unit_num, uom_str

    def _get_uom_id(self, uom_str):
        return self.env['product.uom'].search([
            ('name', '=', str(uom_str).strip().upper()),
        ],
            limit=1,
        )

    def _get_categ_id(self, is_prescription, record):
        """ It returns the product category based on input
        :param is_prescription: bool
        :param record: dict of record. Not used, but good for inherit
        """
        if is_prescription:
            return self.env.ref(
                'medical_prescription_sale.product_category_rx'
            )
        else:
            return self.env.ref(
                'medical_prescription_sale.product_category_otc'
            )

    def _get_medicament_vals(self, record):
        """ It returns a dict of vals for medicament create/write """

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
        gpi = record['gpi']
        is_prescription = False
        dea_code = record['dea'] or '0'

        if cs_ext_id:
            strength_str = cs_ext_id.dn_str.lower().strip()
            route_id = cs_ext_id.route_id.route_id
            form_id = cs_ext_id.form_id.form_id
            gpi = gpi or cs_ext_id.gpi
            is_prescription = cs_ext_id.rx_only_yn

        if not strength_str:
            strength_str = fdb_gcn_seq_id.str.lower().strip()
        if not route_id:
            route_id = fdb_gcn_seq_id.route_id.route_id
        if not form_id:
            form_id = fdb_gcn_seq_id.form_id.form_id
        if not gpi:
            # Just in case there is None or False
            gpi = 0

        strength_num, strength_str = self._get_uom_parts(strength_str)
        strength_uom_id = self._get_uom_id(strength_str)
        sale_uom_id = self._get_uom_id(record['hcfa_unit'] or 'UNIT')
        categ_id = self._get_categ_id(is_prescription, record)

        return {
            'name': medicament_name,
            'drug_route_id': route_id.id,
            'drug_form_id': form_id.id,
            'gpi': str(gpi),
            'control_code': dea_code,
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
            'website_published': True,
        }

    @mapping
    def medicament_id(self, record):

        medicament_obj = self.env['medical.medicament']
        medicament_vals = self._get_medicament_vals(record)
        medicament_id = medicament_obj.search([
            ('name', '=', medicament_vals['name']),
            ('drug_route_id', '=', medicament_vals['drug_route_id']),
            ('drug_form_id', '=', medicament_vals['drug_form_id']),
            ('strength', '=', medicament_vals['strength']),
            ('strength_uom_id', '=', medicament_vals['strength_uom_id']),
        ],
            limit=1,
        )

        if not len(medicament_id):
            try:
                medicament_id = medicament_obj.create(medicament_vals)
            except IntegrityError, e:
                raise ValidationError(_(
                    'Unable to create medicament w/ vals: %s '
                    '--- Original Error: %s'
                ) % (medicament_vals, e))

        else:
            medicament_id[0].write(medicament_vals)

        return {'medicament_id': medicament_id[0].id}

    @mapping
    def lbl_mfg_id(self, record):
        binder = self.binder_for('carepoint.fdb.lbl.rid')
        lbl_rid = binder.to_odoo(record['lblrid'].strip())
        return {'lbl_mfg_id': lbl_rid}

    @mapping
    def carepoint_id(self, record):
        return {'carepoint_id': record['ndc'].strip()}


@carepoint
class FdbNdcImporter(CarepointImporter):
    _model_name = ['carepoint.fdb.ndc']
    _base_mapper = FdbNdcImportMapper

    def _import_dependencies(self):
        """ Import depends for record """
        record = self.carepoint_record
        try:
            self._import_dependency(record['ndc'],
                                    'carepoint.fdb.ndc.cs.ext')
        except IndexError:  # pragma: no cover
            # Won't exist in cs_ext if user_product_yn == 0
            pass
        self._import_dependency(record['gcn_seqno'],
                                'carepoint.fdb.gcn')

    def _after_import(self, binding):
        img_unit = self.unit_for(
            FdbImgIdUnit,
            model='carepoint.fdb.img.id',
        )
        img_unit._import_by_ndc(
            self.carepoint_record['ndc'].strip(),
        )
