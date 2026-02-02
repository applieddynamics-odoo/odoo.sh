{
    'name': 'ADI Custom Confirmation Dialog',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'summary': 'Reusable confirmation dialog wizard',
    'category': 'Tools',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/confirmation_dialog_views.xml',
    ],
    'installable': True,
    'application': False,
}


