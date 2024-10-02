from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    on_time_threshold = fields.Integer('Vendor On Time Delivery Rate')
