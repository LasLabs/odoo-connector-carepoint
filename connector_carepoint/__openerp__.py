# -*- coding: utf-8 -*-
# © 2015 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'CarePoint Connector',
    'description': 'Two-Way Sync With CarePoint',
    'version': '9.0.1.0.0',
    'category': 'Connector',
    'author': "LasLabs",
    'license': 'AGPL-3',
    'website': 'https://laslabs.com',
    'depends': [
        'connector',
        'first_databank',
    ],
    "external_dependencies": {
        "python": [
            'carepoint',
        ],
    },
    'data': [
        'views/carepoint_backend_view.xml',
        'views/connector_menu.xml',
        'data/medical_drug_form_data.xml',
    ],
    'installable': True,
    'application': False,
}
