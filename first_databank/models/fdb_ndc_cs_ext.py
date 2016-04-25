# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbNdcCsExt(models.Model):
    _name = 'fdb.ndc.cs.ext'
    _description = 'Fdb Ndc Cs Ext'

    short_name = fields.Char()
    lot_no = fields.Char()
    orig_mfg = fields.Char()
    pref_gen_yn = fields.Boolean()
    active_yn = fields.Boolean()
    drug_expire_days = fields.Char()
    formulary_yn = fields.Boolean()
    compound_yn = fields.Boolean()
    sup_upd_gen_yn = fields.Boolean()
    sup_upd_phys_yn = fields.Boolean()
    sup_upd_clin_yn = fields.Boolean()
    sup_upd_fin_yn = fields.Boolean()
    sup_upd_med_yn = fields.Boolean()
    dn_form = fields.Char()
    dn_str = fields.Char()
    dn_route = fields.Char()
    rx_only_yn = fields.Boolean()
    manual_yn = fields.Boolean()
    brand_ndc = fields.Char()
    add_user_id = fields.Integer()
    add_date = fields.Datetime()
    chg_user_id = fields.Integer()
    app_flags = fields.Char()
    timestmp = fields.Datetime()
    comp_yn = fields.Boolean()
    dea = fields.Char()
    dea_chg_user = fields.Integer()
    dea_chg_date = fields.Datetime()
    ln = fields.Char()
    ln_chg_user = fields.Integer()
    ln_chg_date = fields.Datetime()
    fdb_chg_date = fields.Datetime()
    ud_svc_code = fields.Char()
    gpi = fields.Char()
    gpi_chg_user = fields.Integer()
    gpi_chg_date = fields.Datetime()
    bill_increment = fields.Integer()
    formula_id = fields.Integer()
    alt_iptside1 = fields.Char()
    alt_iptside2 = fields.Char()
    dose_multiplier = fields.Char()
    default_daw_override = fields.Char()
    manual_price_yn = fields.Boolean()
    compound_type_cn = fields.Integer()
    refrig_cn = fields.Integer()
