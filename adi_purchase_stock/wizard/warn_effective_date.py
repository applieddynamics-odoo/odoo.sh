from odoo import fields, models
from datetime import datetime

class WarnEffectiveDate(models.TransientModel):
    _name = 'warn.effective_date'
    _description = "Remind user to fill in the effective date if they haven't already"

    def button_confirm(self):
        po_id = self.env['purchase.order'].search([('id', '=', self.env.context.get('purchase_order_id'))])
        po_id['effective_date'] = datetime.now()
        po_id.button_done()
