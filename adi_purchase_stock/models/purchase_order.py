from datetime import datetime
from odoo import api, models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _approximate_on_time_rates(self):
        self._cr.execute("UPDATE purchase_order_line SET arrived_late = false;");
        self._cr.execute("""
        UPDATE purchase_order_line pol
            SET arrived_late = true
        FROM purchase_order po
            WHERE po.id = pol.order_id AND
            (
                po.date_order < (SELECT MAX(m.date) FROM stock_move m
                    WHERE m.purchase_line_id = pol.id AND m.state like 'done')
             OR
                (SELECT COUNT(m.id) FROM stock_move m
                    WHERE m.purchase_line_id = pol.id AND m.state like 'done') = 0
            );
        """)
        
    def button_done(self):
        for order in self:
            if not order.effective_date:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'warn.effective_date',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'purchase_order_id': order.id,
                    },
                }
        super().button_done()

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    arrived_late = fields.Boolean(required=True, default=lambda v: False)

    @api.onchange('qty_received')
    def on_change_received(self):
        for r in self:
            # is the product fully received
            if r.product_qty != r.qty_received:
                continue
            # is the product late
            if r.order_line_id.date_order.date() < datetime.now().date():
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'warn.is_po_line_late',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'purchase_order_line_id': r.id,
                    },
                }
