# -*- coding: utf-8 -*-
# from odoo import http


# class FlattenedBom(http.Controller):
#     @http.route('/flattened_bom/flattened_bom', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/flattened_bom/flattened_bom/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('flattened_bom.listing', {
#             'root': '/flattened_bom/flattened_bom',
#             'objects': http.request.env['flattened_bom.flattened_bom'].search([]),
#         })

#     @http.route('/flattened_bom/flattened_bom/objects/<model("flattened_bom.flattened_bom"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('flattened_bom.object', {
#             'object': obj
#         })
