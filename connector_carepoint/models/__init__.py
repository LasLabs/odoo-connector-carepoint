# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
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
from . import stock_warehouse

# Medical Models
from . import medical_patient
from . import medical_physician
from . import medical_prescription_order
from . import medical_prescription_order_line
from . import medical_pathology
from . import medical_pathology_code_type
from . import medical_patient_disease

# Address / Relations
from . import address
from . import address_abstract
from . import address_patient
from . import address_store
from . import address_organization
from . import address_physician

# Phone / Relations
from . import phone
from . import phone_abstract
from . import phone_patient
from . import phone_store
from . import phone_organization
from . import phone_physician

# CarePoint Mappings/Binds
from . import carepoint_account
from . import carepoint_store
from . import carepoint_organization
from . import carepoint_state
from . import carepoint_item
from . import carepoint_vendor

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
