from odoo import fields, models, _
from odoo.exceptions import UserError

class SaleOrderCompleteWizard(models.TransientModel):
    _name = "sale.order.complete.wizard"
    _description = "Sale Order Completion Wizard"

    order_id = fields.Many2one("sale.order", required=True, readonly=True)

    # snapshot (readonly)
    invoice_status = fields.Selection(related="order_id.invoice_status", readonly=True)
    delivery_status = fields.Selection(related="order_id.delivery_status", readonly=True)

    # checks (editable)
    check_invoicing_ok = fields.Boolean(string="Invoicing checked / correct")
    check_deliveries_ok = fields.Boolean(string="Deliveries checked / correct")
    completion_notes = fields.Text(string="Completion notes")

    def action_confirm_complete(self):
        self.ensure_one()

        if not self.check_invoicing_ok or not self.check_deliveries_ok:
            raise UserError(_("Please confirm both Invoicing and Deliveries checks before completing."))

        self.order_id.write({
            "x_adi_completed": True,
            "x_adi_completed_on": fields.Datetime.now(),
            "x_adi_completed_by": self.env.user.id,
        })
        return {"type": "ir.actions.act_window_close"}
