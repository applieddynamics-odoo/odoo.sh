from datetime import datetime
from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        for order in self:
            if order.state == "done" and not order.effective_date:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'warn.effective_date',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'purchase_order_id': order.id,
                    },
                }
        super().button_confirm()
