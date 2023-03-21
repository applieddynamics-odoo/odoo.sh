from odoo import fields, models


class WarnVendorBelowThreshold(models.TransientModel):
    _name = 'warn.vendor.below.threshold'
    _description = 'Require extra confirmation if the vendor is below the on time delivery threshold'

    def _get_purchase_order_ids(self):
        return self.env['purchase.order'].browse(self.env.context.get('purchase_order_ids'))

    purchase_order_ids = fields.Many2many(comodel_name='purchase.order', default=_get_purchase_order_ids)

    def button_confirm(self):
        self.purchase_order_ids.with_context(ignore_threshold=True).button_confirm()
