from datetime import timedelta, datetime
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        if self._context['skip_validation']:
            return super().button_validate()
        for r in self:
            if r.scheduled_date.date() < r.date_done.date():
                sms = self.env['stock.move'].search([('picking_id', '=', r.id)])
                for m in sms:
                    pl = m.purchase_line_id
                    pl['arrived_late'] = True

                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'warn.effective_date',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'stock_picking_id': r.id,
                    },
                }
        return super().button_validate()
