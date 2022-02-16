# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, value):
        date_planned = value.get('date_planned')
        if date_planned:
            dt = datetime.strptime(str(date_planned), '%Y-%m-%d %H:%M:%S')
            value['date_planned'] = dt.replace(hour=12, minute=00)
        res = super().create(value)
        return res

    def write(self, value):
        date_planned = value.get('date_planned')
        if date_planned:
            dt = datetime.strptime(str(date_planned), '%Y-%m-%d %H:%M:%S')
            value['date_planned'] = dt.replace(hour=12, minute=00)
        res = super().write(value)
        return res

    def button_confirm(self):
        for order in self:
            if order.partner_id.should_warn() and not self._context.get('ignore_threshold', False):
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'warn.vendor.below.threshold',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'purchase_order_ids': self.ids,
                    },
                }
        super(PurchaseOrder, self).button_confirm()

