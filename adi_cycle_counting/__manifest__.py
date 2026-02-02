{
    'name':'ADI: Cycle Counting changes',
    'summary':'Add fields to help cycle counting',
    'description':
    """
    Add fields to help cycle counting:
    - Quantity in WIP MOs
    - List of WIP MOs

    Also adds code related to negative inventory correction
    """,
    'website':'',
    'version':'0.1.1',
    'license': 'LGPL-3',
    'author':'ADI/Matthew Younger',
    'category':'Internal Development',

    'depends': ['purchase_stock', 'stock'],
    'data': [
#        'views/purchase_order_views.xml',
#        'views/stock_move_views.xml',
#        'views/stock_picking_views.xml',
#        'views/res_config_settings_views.xml',
#        'views/res_partner_views.xml',
#        'wizard/warn_is_po_line_late_view.xml',
#        'wizard/warn_effective_date.xml',
#        'security/ir.model.access.csv',
    ],
    'assets': {
    },
    'installable':True,
    'application':False,
    'auto_install':False,
}
