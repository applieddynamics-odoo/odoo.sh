# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    on_time_threshold = fields.Integer('Vendor On Time Delivery Rate', related='company_id.on_time_threshold', readonly=False)
