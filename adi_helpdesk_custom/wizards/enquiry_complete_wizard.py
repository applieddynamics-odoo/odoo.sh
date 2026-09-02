from odoo import fields, models


class AdiHelpdeskEnquiryCompleteWizard(models.TransientModel):
    _name = "adi.helpdesk.enquiry.complete.wizard"
    _description = "Complete Customer Enquiry"

    enquiry_id = fields.Many2one(
        "adi.helpdesk.enquiry",
        string="Customer Enquiry",
        required=True,
        readonly=True,
    )

    def action_confirm(self):
        self.ensure_one()

        self.enquiry_id.action_complete_confirmed()

        return {
            "type": "ir.actions.act_window_close",
        }