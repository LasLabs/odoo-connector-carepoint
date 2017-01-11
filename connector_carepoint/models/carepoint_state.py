# -*- coding: utf-8 -*-
# Copyright 2015-2017 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class CarepointState(models.Model):
    _name = 'carepoint.state'
    _description = 'Carepoint State'
    name = fields.Char(required=True)
    code = fields.Integer(required=True)
    order_state = fields.Char(required=True)
    invoice_state = fields.Char(required=True)
    prescription_state = fields.Char(required=True)
