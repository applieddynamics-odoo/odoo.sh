from odoo import fields, models
from datetime import datetime

class WarnIsPOLineLate(models.TransientModel):
    _name = 'warn.is_po_line_late'
    _description = "Check whether a PO line was really late if it is filled in late"

    def button_confirm(self):
        pol_id = self.env['purchase.order.line'].search([('id', '=', self.env.context.get('purchase_order_id'))])
        pol_id['arrived_late'] = True
