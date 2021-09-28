# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        for order in self:
            if order.partner_id.on_time_rate <= order.company_id.on_time_threshold and not self.env.context.get('ignore_threshold'):
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'warn.vendor.below.threshold',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'purchase_order_ids': self.ids,
                    },
                }
        super(PurchaseOrder, self).button_confirm()
