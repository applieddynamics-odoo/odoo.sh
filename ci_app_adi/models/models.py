# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class ci_app_adi(models.Model):
#     _name = 'ci_app_adi.ci_app_adi'
#     _description = 'ci_app_adi.ci_app_adi'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
