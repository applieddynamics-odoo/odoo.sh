# -*- coding: utf-8 -*-
# from odoo import http


# class AdiAgedReceivables(http.Controller):
#     @http.route('/adi_aged_receivables/adi_aged_receivables', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/adi_aged_receivables/adi_aged_receivables/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('adi_aged_receivables.listing', {
#             'root': '/adi_aged_receivables/adi_aged_receivables',
#             'objects': http.request.env['adi_aged_receivables.adi_aged_receivables'].search([]),
#         })

#     @http.route('/adi_aged_receivables/adi_aged_receivables/objects/<model("adi_aged_receivables.adi_aged_receivables"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('adi_aged_receivables.object', {
#             'object': obj
#         })
