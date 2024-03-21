from datetime import timedelta, datetime
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for r in self:
            if r.scheduled_date < r.date_done:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'warn.effective_date',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'stock_picking_id': r.id,
                    },
                }
        super().button_validate()
