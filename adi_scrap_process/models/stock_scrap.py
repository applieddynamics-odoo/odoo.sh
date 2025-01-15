# -*- coding: utf-8 -*-
from odoo import _, models, fields, api
from datetime import datetime

class StockScrap(models.Model):
    _inherit = "stock.scrap"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('done', 'Done')],
        string='Status', default="draft", readonly=True, tracking=True)

    def action_approve(self):
        self.ensure_one()
        if float_is_zero(self.scrap_qty,
                         precision_rounding=self.product_uom_id.rounding):
            raise UserError(_('You can only enter positive quantities.'))
        self["state"] = "approved"
