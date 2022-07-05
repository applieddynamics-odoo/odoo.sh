# -*- coding: utf-8 -*-

{
    'name': 'ADI: Warning Msg Upon PO Confirmation If the On Rate is =< threshold value',
    'summary': 'ADI: Warning Msg Upon PO Confirmation If the On Rate is =< threshold value',
    'sequence': 100,
    'license': 'OPL-1',
    'website': 'https://www.odoo.com',
    'version': '15.0.1.0.1',
    'author': 'Odoo Inc',
    'description': """
        Task ID: 2648487
        - Add Warning when on time percent is less than threshold
    """,
    'category': 'Custom Development',

    # any module necessary for this one to work correctly
    'depends': ['purchase_stock','web'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'views/stock_move_views.xml',
        'views/stock_picking_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/warn_vendor_below_threshold_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'adi_purchase_stock/static/src/js/form_controller.js'
        ]
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
