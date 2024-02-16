# -*- coding: utf-8 -*-
# from odoo import http


# class FlatBom(http.Controller):
#     @http.route('/flat_bom/flat_bom', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/flat_bom/flat_bom/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('flat_bom.listing', {
#             'root': '/flat_bom/flat_bom',
#             'objects': http.request.env['flat_bom.flat_bom'].search([]),
#         })

#     @http.route('/flat_bom/flat_bom/objects/<model("flat_bom.flat_bom"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('flat_bom.object', {
#             'object': obj
#         })
