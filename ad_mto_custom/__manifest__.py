# -*- coding: utf-8 -*-
{
    'name': "Custom MTO/PO quantity",

    'summary': """
        This module is to create RFQ qty for the product should consider the 'Forecasted qty'.
        As well as change the components quantity and rerun the Manufacturing order.
    """,

    'description': """
        Task id:  2658636
        This module is to create RFQ qty for the product should consider the 'Forecasted qty'.
    """,
    'author': 'Odoo Ps',
    'version': '1.0.0',

    'depends': ['sale_management', 'stock', 'purchase', 'mrp'],

    'data': [
        'views/mrp_production.xml',
    ],

    'installable': True,
}
