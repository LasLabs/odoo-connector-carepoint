# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Website Medicament First Databank',
    'description': 'Uses FDB Monograph data to generate website product '
                   'descriptions.',
    'version': '10.0.1.0.0',
    'category': 'Connector',
    'author': "LasLabs",
    'license': 'AGPL-3',
    'website': 'https://laslabs.com',
    'depends': [
        'connector_carepoint',
        'website_sale',
        'website_portal_medical_patient_species',
    ],
    'data': [
        'views/carepoint_backend_view.xml',
        'wizards/website_fdb_medicament_description_view.xml',
        'data/website_medicament_description_template.xml',
        'security/ir.model.access.csv',
        'security/medical_patient_security.xml',
    ],
    'installable': True,
    'application': False,
}
