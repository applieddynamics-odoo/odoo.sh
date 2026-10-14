from markupsafe import Markup, escape

from datetime import timedelta
from odoo import fields, models

from odoo.exceptions import UserError


class AdiHelpdeskCloseWizard(models.TransientModel):
    _name = "adi.helpdesk.close.wizard"
    _description = "Submit Helpdesk Ticket for Customer Review"

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

        review_stage = self.env["helpdesk.stage"].search(
            [
                ("name", "=", "Awaiting Customer Review"),
                ("team_ids", "in", [self.ticket_id.team_id.id]),
            ],
            limit=1,
        )

        if not review_stage:
            raise UserError(
                "Could not find the 'Awaiting Customer Review' "
                "stage for this Helpdesk team."
            )

        # One minute for staging tests.
        # Change to timedelta(hours=48) after validation.
        review_deadline = fields.Datetime.now() + timedelta(minutes=1)

        ticket = self.ticket_id

        # Save the latest closure information first.
        ticket.write({
            "adi_closure_result": self.adi_closure_result,
            "adi_closure_statement": self.adi_closure_statement,
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
                    <strong>Resolution Submitted for Customer Review</strong>
                </p>

                <p>
                    ADI considers your support request resolved.
                    Please review the resolution below and reply to
                    this email only if further action is required.
                </p>

                <p>
                    <strong>Result:</strong>
                    {closure_result}
                </p>

                <p>
                    <strong>Closure statement:</strong>
                    {closure_statement}
                </p>

                <p>
                    <em>
                        If no further action is required, this ticket
                        will be closed after 48 hours.
                    </em>
                </p>
            </div>
        """).format(
            closure_result=escape(closure_result_label),
            closure_statement=closure_statement_html,
        )

        # Submit for customer review instead of closing immediately.
        ticket.write({
            "stage_id": review_stage.id,
            "adi_closure_review_deadline": review_deadline,
            "adi_closure_review_required": False,
        })

        # Customer-facing resolution notification.
        ticket.message_post(
            body=message_body,
            subject=ticket._adi_email_subject("Customer Review"),
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )

        # Internal audit trail. Do not notify the customer.
        ticket.message_post(
            body=Markup(
                "<strong>Closure submitted for customer review.</strong>"
                "<p>Automatic closure scheduled for: {deadline} UTC</p>"
            ).format(
                deadline=escape(
                    review_deadline.strftime("%d %b %Y %H:%M")
                ),
            ),
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )

        return {"type": "ir.actions.act_window_close"}