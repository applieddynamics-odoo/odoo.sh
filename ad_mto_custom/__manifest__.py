# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Custom MTO/PO quantity",

    'summary': """
        This module is to create RFQ qty for the product should consider the 'Forecasted qty'.
    """,

    'description': """
        Task id:  2658636
        This module is to create RFQ qty for the product should consider the 'Forecasted qty'.
    """,
    'author': 'Odoo Ps',
    'version': '1.0.0',

    'depends': ['sale_management', 'stock', 'purchase', 'mrp'],

    'installable': True,
}
