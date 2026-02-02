{
    'name':'ADI: Scrap Process Changes',
    'summary':'Add new state between draft and done',
    'description':
    """
    Add new state "Approved" between draft and done.
    This separates approval and actually performing the stock moves.
    """,
    'website':'',
    'version':'0.0.1',
    'license': 'LGPL-3',
    'author':'ADI/Matthew Younger',
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
