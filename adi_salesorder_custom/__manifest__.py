{
    'name': 'ADI Sales Order Customisations',
    'version': '17.0.1.0.0',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
