# -*- coding: utf-8 -*-

{
    'name': 'ADI: Warning Msg Upon PO Confirmation If the On Rate is =< threshold value',
    'summary': 'ADI: Warning Msg Upon PO Confirmation If the On Rate is =< threshold value',
    'sequence': 100,
    'license': 'OEEL-1',
    'website': 'https://www.odoo.com',
    'version': '1.1',
    'author': 'Odoo Inc',
    'description': """
        Task ID: 2648487
        - Add Warning when on time percent is less than threshold
    """,
    'category': 'Custom Development',

    # any module necessary for this one to work correctly
    'depends': ['purchase_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'wizard/warn_vendor_below_threshold_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
