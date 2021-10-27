# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WarnVendorBelowThreshold(models.TransientModel):
    _name = 'warn.vendor.below.threshold'
    _description = 'Require extra confirmation if the vendor is below the on time delivery threshold'

    def _get_purchase_order_ids(self):
        return self.env['purchase.order'].browse(self.env.context.get('purchase_order_ids'))

    def _get_action(self):
        return self.env.context.get('action')

    purchase_order_ids = fields.Many2many(comodel_name='purchase.order', default=_get_purchase_order_ids)
    action = fields.Selection(selection=[('write', 'Write'), ('confirm', 'Confirm')], default=_get_action)

    def button_confirm(self):
        if self.action == 'write':
            self.purchase_order_ids.with_context(ignore_threshold=True).write(self.env.context.get('vals'))
        else:
            self.purchase_order_ids.with_context(ignore_threshold=True).button_confirm()
