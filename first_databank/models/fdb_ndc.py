# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class FdbNdc(models.Model):
    _name = 'fdb.ndc'
    _description = 'Fdb Ndc'
    _inherits = {'medical.medicament.ndc': 'ndc_id'}

    ndc_id = fields.Many2one(
        string='Medical NDC',
        comodel_name='medical.medicament.ndc',
        ondelete='cascade',
        required=True,
    )
    lbl_mfg_id = fields.Many2one(
        string='Label Manufacturer',
        comodel_name='fdb.lbl.rid',
    )
    lblrid = fields.Char()
    gcn_seqno = fields.Char()
    ps = fields.Char()
    df = fields.Char()
    ad = fields.Char()
    ln = fields.Char(
        help='Display Name',
    )
    bn = fields.Char(
        help='Name',
    )
    pndc = fields.Char()
    repndc = fields.Char()
    ndcfi = fields.Char()
    daddnc = fields.Char()
    dupdc = fields.Char()
    desi = fields.Char()
    desdtec = fields.Char()
    desi2 = fields.Char()
    des2dtec = fields.Char()
    dea = fields.Char(
        help='DEA Scheduling',
    )
    cl = fields.Char()
    gpi = fields.Char(
        help='GPI',
    )
    hosp = fields.Char()
    innov = fields.Char()
    ipi = fields.Char()
    mini = fields.Char()
    maint = fields.Char()
    obc = fields.Char()
    obsdtec = fields.Char()
    ppi = fields.Char()
    stpk = fields.Char()
    repack = fields.Char()
    top200 = fields.Char()
    ud = fields.Char()
    csp = fields.Char()
    color = fields.Char(
        help='Color',
    )
    flavor = fields.Char(
        help='Flavor',
    )
    shape = fields.Char(
        help='Shape',
    )
    ndl_gdge = fields.Char(
        help='Needle gauge'
    )
    ndl_lngth = fields.Char(
        help='Needle Length',
    )
    syr_cpcty = fields.Char(
        help='Syringe Capacity',
    )
    shlf_pck = fields.Char()
    shipper = fields.Char()
    skey = fields.Char()
    hcfa_fda = fields.Char()
    hcfa_unit = fields.Char()
    hcfa_ps = fields.Char()
    hcfa_appc = fields.Char()
    hcfa_mrkc = fields.Char()
    hcfa_trmc = fields.Char()
    hcfa_typ = fields.Char()
    hcfa_desc1 = fields.Char()
    hcfa_desi1 = fields.Char()
    uu = fields.Char()
    pd = fields.Char()
    ln25 = fields.Char()
    ln25i = fields.Char()
    gpidc = fields.Char()
    bbdc = fields.Char()
    home = fields.Char()
    inpcki = fields.Char()
    outpcki = fields.Char()
    obc_exp = fields.Char()
    ps_equiv = fields.Char()
    plblr = fields.Char()
    hcpc = fields.Char()
    top50gen = fields.Char()
    obc3 = fields.Char()
    gmi = fields.Char()
    gni = fields.Char()
    gsi = fields.Char()
    gti = fields.Char()
    ndcgi1 = fields.Char()
    user_gcdf = fields.Char()
    user_str = fields.Char()
    real_product_yn = fields.Boolean()
    no_update_yn = fields.Boolean()
    no_prc_update_yn = fields.Boolean()
    user_product_yn = fields.Char()
    cpname_short = fields.Char()
    status_cn = fields.Char()
    update_yn = fields.Boolean()
    active_yn = fields.Boolean(
        help='Is Active?',
    )
    ln60 = fields.Char()
