from odoo import fields, models
from datetime import datetime

class WarnEffectiveDate(models.TransientModel):
    _name = 'warn.effective_date'
    _description = "Ensure that the delivery is correctly being marked as late/on time"

    def button_change(self):
        sp_id = self.env['stock.picking'].search([('id', '=', self.env.context.get('stock_picking_id'))])
        sms = self.env['stock.move'].search([('picking_id', '=', sp_id.id)])
        for m in sms:
            pl = m.purchase_line_id
            pl['arrived_late'] = False
        raise Exception(sp_id, sms)
        sp_id.with_context(skip_validation=True).button_validate()
