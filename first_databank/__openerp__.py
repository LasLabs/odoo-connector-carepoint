# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'First Databank',
    'description': 'Provides base models for storage of First Databank data',
    'version': '9.0.1.0.0',
    'category': 'Connector',
    'author': "LasLabs",
    'license': 'AGPL-3',
    'website': 'https://laslabs.com',
    'depends': [
        'sale_stock',
        'medical_prescription_sale_stock',
        'medical_insurance_us',
        'medical_medication_us',
        # 'medical_patient_us',
        'medical_physician_us',
        'medical_pharmacy_us',
        'medical_prescription_us',
        'medical_manufacturer',
    ],
    'installable': True,
    'application': False,
}
