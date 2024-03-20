from odoo import fields, models
from datetime import datetime

class WarnEffectiveDate(models.TransientModel):
    _name = 'warn.effective_date'
    _description = "Ensure that the delivery is correctly being marked as late/on time"

    def button_change(self):
        sp_id = self.env['stock.picking'].search([('id', '=', self.env.context.get('stock_picking_id'))])
        sp_id['date_done'] = sp_id.scheduled_date
        sp_id.button_validate()
