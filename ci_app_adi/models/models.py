# -*- coding: utf-8 -*-

 from odoo import models, fields, api


class ci_app_adi(models.Model):
    _name = 'ci_app_adi.ci_app_adi'
    _description = 'ADI CI and CAR App'

    title = fields.Char()
    description = fields.Text()
    action_type = fields.Selection([("CI", "CI"), ("CAR", "CAR")])
    status = fields.Selection([("Open", "Open"),
                               ("Assigned", "Assigned"),
                               ("Done", "Done")])
    assignee = fields.Many2one("res.users")




