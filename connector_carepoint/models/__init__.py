# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# Backend
from . import carepoint_backend

# Base Models
from . import res_users
from . import sale_order
from . import sale_order_line
from . import procurement_order
from . import account_invoice_line
from . import stock_picking

# Medical Models
from . import medical_pharmacy
from . import medical_patient
from . import medical_physician
from . import medical_medicament
from . import medical_prescription_order
from . import medical_prescription_order_line

# Address / Relations
from . import address
from . import address_patient
from . import address_pharmacy
from . import address_physician

# CarePoint Mappings/Binds
from . import account
from . import carepoint_state

# FDB
from . import fdb_ndc
from . import fdb_route
from . import fdb_form
from . import fdb_gcn
from . import fdb_gcn_seq
from . import fdb_ndc_cs_ext
from . import fdb_lbl_rid
from . import fdb_img
from . import fdb_img_id
from . import fdb_img_mfg
from . import fdb_img_date
from . import fdb_unit
from . import fdb_pem_moe
from . import fdb_pem_mogc
