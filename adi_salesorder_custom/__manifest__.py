{
    'name': 'ADI Sales Order Customisations',
    "license": "LGPL-3",
    "summary": "Sales App custom module ",    
    'version': '17.0.1.0.0',
    "author": "Paul Davies",
    'depends': ['sale', 'sale_stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/sale_order_complete_wizard_views.xml',
    ],

    'installable': True,
    'application': False,
}

