# -*- coding: utf-8 -*-
from odoo import _, models, fields, api
from datetime import datetime

class StockScrap(models.Model):
    _inherit = "stock.scrap"

    approval_manager = fields.Many2one("res.user")
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('awaiting_approval', "Awaiting Approval"),
        ('approved', 'Approved'),
        ('done', 'Done')],
        string='Status', default="draft", readonly=True, tracking=True)

    def action_request_approval(self):
        self.ensure_one()
        if float_is_zero(self.scrap_qty, precision_rounding=self.product_uom_id.rounding):
            raise UserError(_('You can only enter positive quantities.'))
        self["state"] = "awaiting_approval"
        # TODO: send out email to relevant person
    
    def action_approve(self):
        self.ensure_one()
        if float_is_zero(self.scrap_qty, precision_rounding=self.product_uom_id.rounding):
            raise UserError(_('You can only enter positive quantities.'))
        self["state"] = "approved"
