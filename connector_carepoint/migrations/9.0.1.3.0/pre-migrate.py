# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    try:
        cr.execute('ALTER TABLE carepoint_medical_prescription_order_line '
                   'RENAME TO carepoint_rx_ord_ln')
    except Exception:
        cr.rollback()
        _logger.exception('Cannot perform migration')

    try:
        cr.execute('ALTER TABLE carepoint_carepoint_organization '
                   'RENAME TO carepoint_org_bind')
    except Exception:
        cr.rollback()
        _logger.exception('Cannot perform migration')
