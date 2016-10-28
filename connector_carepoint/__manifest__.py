# -*- coding: utf-8 -*-
# Copyright 2015-2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'CarePoint Connector',
    'description': 'Two-Way Sync With CarePoint',
    'version': '10.0.1.0.0',
    'category': 'Connector',
    'author': "LasLabs",
    'license': 'AGPL-3',
    'website': 'https://laslabs.com',
    'depends': [
        'connector',
        'first_databank',
        'medical_physician_us',
        'delivery',
        'l10n_multilang',
        'l10n_us',
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
        'data/carepoint_state_data.xml',
        'data/carepoint_carepoint_account_data.xml',
        'data/ir_cron_data.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
