from markupsafe import Markup, escape

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

        closed_stage = self.env["helpdesk.stage"].search(
            [("name", "=", "Closed")],
            limit=1,
        )

        if not closed_stage:
            raise UserError(
                "Could not find a Helpdesk stage called 'Closed'."
            )

        ticket = self.ticket_id

        ticket.write({
            "stage_id": closed_stage.id,
            "adi_closure_result": self.adi_closure_result,
            "adi_closure_statement": self.adi_closure_statement,
            "close_date": fields.Datetime.now(),
        })

        closure_result_labels = dict(
            self._fields["adi_closure_result"].selection
        )
        closure_result_label = closure_result_labels.get(
            self.adi_closure_result,
            self.adi_closure_result,
        )

        statement_lines = (
            self.adi_closure_statement or ""
        ).splitlines()

        closure_statement_html = Markup("<br/>").join(
            escape(line) for line in statement_lines
        )

        message_body = Markup("""
            <div>
                <p>
                    <strong>Ticket Closed</strong>
                </p>

                <p>
                    Your support request has now been completed.
                </p>

                <p>
                    <strong>Closure result</strong><br/>
                    {closure_result}
                </p>

                <p>
                    <strong>Closure statement</strong><br/>
                    {closure_statement}
                </p>

                <p>
                    You will shortly receive an email inviting you to rate
                    the support you received.
                </p>
            </div>
        """).format(
            closure_result=escape(closure_result_label),
            closure_statement=closure_statement_html,
        )

        ticket.message_post(
            body=message_body,
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )

        return {"type": "ir.actions.act_window_close"}