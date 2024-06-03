
from datetime import datetime
from odoo import api, models, fields

"""
        UPDATE purchase_order_line pol
            SET arrived_late = true
        FROM purchase_order po
            WHERE                
                pol.order_id = po.id AND 
                (
                    po.date_order < (SELECT MAX(sp.date_done)
                                     FROM stock_move m JOIN stock_picking sp
                                     ON m.picking_id = sp.id
                                     WHERE m.purchase_line_id = pol.id
                                     AND m.state = 'done')
                OR
                    (pol.product_qty > (SELECT SUM(m.product_qty)
                                        FROM stock_move m JOIN stock_picking sp
                                        on m.picking_id = sp.id
                                        WHERE m.purchase_line_id = pol.id
                                        AND m.state = 'done')
                    AND po.date_order::date < '%s'::date)
                );
... % (datetime.now().strftime("%Y-%m-%d"))
"""

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _approximate_on_time_rates(self):
        self._cr.execute("UPDATE purchase_order_line SET arrived_late = false;");
        self._cr.execute("""
        UPDATE purchase_order_line pol
            SET arrived_late = true
        WHERE                
            (SELECT BOOL_OR(date(sp.date_done) > pol.date_planned OR (CURRENT_DATE > pol.date_planned AND sp.date_done IS NULL))
                   FROM stock_move m JOIN stock_picking sp
                   ON m.picking_id = sp.id
                   WHERE m.purchase_line_id = pol.id
                   AND m.state = 'done') = true
             AND pol.product_qty > 0;
        """)

        
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    arrived_late = fields.Boolean(required=True, default=lambda v: False)

    def action_mark_late(self):
        for r in self:
            r['arrived_late'] = True

    def action_unmark_late(self):
        for r in self:
            r['arrived_late'] = False
