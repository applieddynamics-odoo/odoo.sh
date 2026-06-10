from odoo import fields, models


class AdiHelpdeskConfirmEmailBlockWizard(models.TransientModel):
    _name = "adi.helpdesk.confirm.email.block.wizard"
    _description = "Confirm Helpdesk Email Block"

    wizard_id = fields.Many2one(
        "adi.helpdesk.review.validity.wizard",
        string="Review Validity Wizard",
        required=True,
        readonly=True,
    )

    def action_confirm(self):
        self.ensure_one()
        return self.wizard_id.action_mark_spam_confirmed()