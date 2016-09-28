# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute("""SELECT 1
                FROM information_schema.columns
               WHERE table_name='carepoint_medical_patient_disease'
           """)
    if cr.rowcount:
        cr.execute('ALTER TABLE carepoint_medical_patient_disease '
                   'RENAME TO carepoint_carepoint_patient_disease')
