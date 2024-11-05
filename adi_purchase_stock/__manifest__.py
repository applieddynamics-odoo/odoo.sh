{
    'name':'ADI: Warning Msg Upon PO Confirmation If the On Rate is =< threshold value',
    'summary':'ADI: Warning Msg Upon PO Confirmation If the On Rate is =< threshold value',
    'description':
    """
        Task ID: 2648487
        - Add Warning when on time percent is less than threshold	
    """,
    'sequence':100,
    'license':'OPL-1',
    'website':'https://www.adi.com',
    'version':'1.1.1',
    'author':'Odoo, Inc AND Matthew Younger of ADI',
    'category':'Custom Development',

    # any module necessary for this one to work correctly
    'depends': ['purchase_stock'],
    'data': [
        'views/purchase_order_views.xml',
        'views/stock_move_views.xml',
        'views/stock_picking_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'wizard/warn_is_po_line_late_view.xml',
        'wizard/warn_effective_date.xml',
        'security/ir.model.access.csv',
    ],
    'installable':True,
    'application':False,
    'auto_install':False,
}
