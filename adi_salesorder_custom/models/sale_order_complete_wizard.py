from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrderCompleteWizard(models.TransientModel):
    _name = "sale.order.complete.wizard"
    _description = "Sale Order Completion Wizard"

    order_id = fields.Many2one("sale.order", required=True, readonly=True)

    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sales Order",
        required=True,
        readonly=True,
    )

    # Snapshot info (readonly)
    invoice_status = fields.Selection(related="order_id.invoice_status", readonly=True)
    delivery_status = fields.Selection(related="order_id.delivery_status", readonly=True)

    # Checks (editable)
    check_invoicing_ok = fields.Boolean(string="Invoicing checked / correct", required=False)
    check_deliveries_ok = fields.Boolean(string="Deliveries checked / correct", required=False)
    completion_notes = fields.Text(string="Completion notes")

    def action_confirm_complete(self):
        self.ensure_one()

        # enforce checks (simple first pass)
        if not self.check_invoicing_ok or not self.check_deliveries_ok:
            raise UserError(_("Please confirm both Invoicing and Deliveries checks before completing."))

        self.order_id.write({
            "x_adi_completed": True,
            "x_adi_completed_on": fields.Datetime.now(),
            "x_adi_completed_by": self.env.user.id,
            # optional: store notes somewhere on SO (add field if you want)
            # "x_adi_completion_notes": self.completion_notes,
        })
        return {"type": "ir.actions.act_window_close"}

