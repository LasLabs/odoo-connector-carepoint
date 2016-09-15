# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute('ALTER TABLE carepoint_medical_prescription_order_line '
               'RENAME TO carepoint_rx_ord_ln')

    cr.execute('ALTER TABLE carepoint_carepoint_organization '
               'RENAME TO carepoint_org_bind')
