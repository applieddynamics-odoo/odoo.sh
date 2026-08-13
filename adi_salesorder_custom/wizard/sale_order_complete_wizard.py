# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrderCompleteWizard(models.TransientModel):
    _name = "sale.order.complete.wizard"
    _description = "Sale Order Completion Wizard"

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Order",
        required=True,
        readonly=True,
    )
    invoice_status = fields.Selection(related="sale_order_id.invoice_status", readonly=True)
    delivery_status = fields.Selection(related="sale_order_id.delivery_status", readonly=True)

    x_adi_invoice_status_text = fields.Char(string="Invoice Status", readonly=True)
    x_adi_delivery_status_text = fields.Char(string="Delivery Status", readonly=True)

    x_adi_check_invoicing_ok = fields.Boolean(string="Invoicing checked / correct")
    x_adi_check_deliveries_ok = fields.Boolean(string="Deliveries checked / correct")
    x_adi_completion_notes = fields.Text(string="Completion notes")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        so_id = self.env.context.get("default_sale_order_id") or self.env.context.get("active_id")
        if not so_id:
            return res

        so = self.env["sale.order"].browse(so_id).exists()
        if not so:
            return res

        res["sale_order_id"] = so.id

        # Human-friendly selection labels
        if "x_adi_invoice_status_text" in fields_list:
            res["x_adi_invoice_status_text"] = dict(so._fields["invoice_status"].selection).get(
                so.invoice_status, so.invoice_status
            )

        if "x_adi_delivery_status_text" in fields_list:
            res["x_adi_delivery_status_text"] = dict(so._fields["delivery_status"].selection).get(
                so.delivery_status, so.delivery_status
            )

        return res

    def _post_completion_message(self, sale_order):
        """Post a standard chatter note on the sales order."""
        self.ensure_one()

        lines = ["<p><b>Sales order marked complete via wizard.</b></p>"]
        lines.append("<ul>")
        lines.append(f"<li>Invoicing checked / correct: {'Yes' if self.x_adi_check_invoicing_ok else 'No'}</li>")
        lines.append(f"<li>Deliveries checked / correct: {'Yes' if self.x_adi_check_deliveries_ok else 'No'}</li>")
        lines.append("</ul>")

        if self.x_adi_completion_notes:
            # preserve line breaks
            notes_html = "<br/>".join((self.x_adi_completion_notes or "").splitlines())
            lines.append(f"<p><b>Completion notes:</b><br/>{notes_html}</p>")

        sale_order.message_post(
            body="".join(lines),
            subtype_xmlid="mail.mt_note",
        )

    def action_confirm_complete(self):
        """Called by the wizard button: Confirm Complete."""
        self.ensure_one()

        sale_order = self.sale_order_id.exists()
        if not sale_order:
            return {"type": "ir.actions.act_window_close"}

        # For now: just log the completion checks + notes to chatter.
        # If you later want to implement actual 'completion' logic
        # (e.g., set a custom flag/stage), do it here.
        self._post_completion_message(sale_order)

        return {"type": "ir.actions.act_window_close"}

    
    


