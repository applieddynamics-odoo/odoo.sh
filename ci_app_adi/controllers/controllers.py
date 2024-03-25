# -*- coding: utf-8 -*-
# from odoo import http


# class CiAppAdi(http.Controller):
#     @http.route('/ci_app_adi/ci_app_adi', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ci_app_adi/ci_app_adi/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ci_app_adi.listing', {
#             'root': '/ci_app_adi/ci_app_adi',
#             'objects': http.request.env['ci_app_adi.ci_app_adi'].search([]),
#         })

#     @http.route('/ci_app_adi/ci_app_adi/objects/<model("ci_app_adi.ci_app_adi"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ci_app_adi.object', {
#             'object': obj
#         })
