# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class CarepointState(models.Model):
    _name = 'carepoint.state'
    _description = 'Carepoint State'
    name = fields.Char(required=True)
    code = fields.Integer(required=True)
    order_state = fields.Char(required=True)
    prescription_state = fields.Char(required=True)
