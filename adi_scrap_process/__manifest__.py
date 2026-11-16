{
    'name':'ADI: Scrap Process Changes',
    'summary':'Add new state between draft and done',
    'description':
    """
    Add new state "Approved" between draft and done.
    This separates approval and actually performing the stock moves.
    """,
    'website':'',
    "version": "19.0.1.0.0",
    'license': 'LGPL-3',
    'author':'Paul Davies',
    'category':'Internal Development',

    'depends': ['stock'],
    'data': [
        'views/stock_scrap_views.xml'
    ],
    'assets': {
    },
    'installable':True,
    'application':False,
    'auto_install':False,
}
