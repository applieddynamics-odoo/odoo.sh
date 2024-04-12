from datetime import timedelta, datetime
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        if self._context.get('skip_validation'):
            return super().button_validate()
        for r in self:
            sms = self.env['stock.move'].search([('picking_id', '=', r.id)])
            if len(sms) > 1:
                raise Exception("Please email myounger@adi.com with this error")
            po = sms[0].purchase_line_id.order_id
            if po.date_planned.date() < r.date_done.date():
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
