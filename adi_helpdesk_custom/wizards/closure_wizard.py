from odoo import fields, models
from odoo.exceptions import UserError

class AdiHelpdeskCloseWizard(models.TransientModel):
    _name = "adi.helpdesk.close.wizard"
    _description = "Close Helpdesk Ticket"

    ticket_id = fields.Many2one(
        "helpdesk.ticket",
        string="Ticket",
        required=True,
        readonly=True,
    )

    adi_closure_result = fields.Selection(
        [
            ("resolved_fault_fixed", "Resolved - fault fixed"),
            ("resolved_user_guidance", "Resolved - user guidance"),
            ("no_fault_found", "No fault found"),
            ("out_of_scope", "Out of scope"),
            ("duplicate", "Duplicate"),
            ("cancelled", "Cancelled"),
        ],
        string="Resolution Category",
        required=True,
    )
    
    adi_closure_statement = fields.Text(
        string="Closure Statement",
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()

        closed_stage = self.env["helpdesk.stage"].search([
            ("name", "=", "Closed")
        ], limit=1)

        if not closed_stage:
            raise UserError("Could not find a Helpdesk stage called 'Closed'.")

        self.ticket_id.write({
            "stage_id": closed_stage.id,
            "adi_closure_result": self.adi_closure_result,
            "adi_closure_statement": self.adi_closure_statement,
            "close_date": fields.Datetime.now(),
        })

        return {"type": "ir.actions.act_window_close"}
    

