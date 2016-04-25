# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import openerp.addons.connector.backend as backend


carepoint = backend.Backend('carepoint')
carepoint299 = backend.Backend(parent=carepoint, version='2.99')
