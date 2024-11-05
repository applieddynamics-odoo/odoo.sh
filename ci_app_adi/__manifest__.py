# -*- coding: utf-8 -*-
{
    'name': "ci_app_adi",

    'summary': """
         ADI's CI/CAR App
    """,

    'description': """
         ADI's CI/CAR App
    """,

    'author': "Matt Y/ADI",
    'website': "https://adi.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'mail'],

    # always loaded
    'data': [
#        'views/views.xml',
        'data/sequences.xml',
        'reports/templates.xml',
        'reports/reports.xml',
        'security/ir.model.access.csv'
    ],
}
