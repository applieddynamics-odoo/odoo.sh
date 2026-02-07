from odoo import api, fields, models, _

class SaleOrderCompleteWizard(models.TransientModel):
    _name = "sale.order.complete.wizard"
    _description = "Sale Order Completion Wizard"

    sale_order_id = fields.Many2one("sale.order", required=True, readonly=True)

    check_invoicing = fields.Char(readonly=True)
    check_delivery = fields.Char(readonly=True)

    notes = fields.Text(string="Completion Notes")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        order = self.env["sale.order"].browse(self.env.context.get("default_sale_order_id"))
        if order:
            res["sale_order_id"] = order.id

            # Invoicing check (sale + account)
            # invoice_status: 'no', 'to invoice', 'invoiced', 'upselling'
            inv = order.invoice_status
            if inv == "invoiced":
                res["check_invoicing"] = _("OK - Fully invoiced")
            elif inv == "to invoice":
                res["check_invoicing"] = _("NOT OK - Still to invoice")
            elif inv == "upselling":
                res["check_invoicing"] = _("Review - Upselling opportunity")
            else:
                res["check_invoicing"] = _("Review - Not invoiced")

            # Delivery check (sale_stock)
            pending = order.picking_ids.filtered(lambda p: p.state not in ("done", "cancel"))
            if not order.picking_ids:
                res["check_delivery"] = _("Review - No pickings found")
            elif pending:
                res["check_delivery"] = _("NOT OK - Pending deliveries exist (%s)") % len(pending)
            else:
                res["check_delivery"] = _("OK - All deliveries done/cancelled")

        return res

    def action_confirm_complete(self):
        self.ensure_one()
        self.sale_order_id.action_mark_completed(notes=self.notes)
        return {"type": "ir.actions.act_window_close"}
