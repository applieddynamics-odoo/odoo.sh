from odoo import fields, models


class AdiHelpdeskEnquiry(models.Model):
    _name = "adi.helpdesk.enquiry"
    _description = "Helpdesk Customer Enquiry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Subject",
        required=True,
        tracking=True,
    )

    contact_name = fields.Char(
        string="Contact Name",
    )

    company_name = fields.Char(
        string="Company Name",
    )

    email = fields.Char(
        string="Email",
        required=True,
        tracking=True,
    )

    phone = fields.Char(
        string="Phone",
    )

    message = fields.Text(
        string="Message",
    )

    state = fields.Selection(
        [
            ("new", "New"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="new",
        required=True,
        tracking=True,
        copy=False,
    )

    closure_reason = fields.Selection(
        [
            ("completed", "Completed"),
            ("blocked", "Blocked"),
        ],
        string="Closure Reason",
        readonly=True,
        copy=False,
        tracking=True,
    )

    def action_complete(self):
        """
        Close an enquiry after the manager has completed any
        required manual actions, such as creating the Contact
        and raising a Helpdesk ticket.
        """

        for enquiry in self:
            enquiry.write({
                "state": "closed",
                "closure_reason": "completed",
            })

            enquiry.message_post(
                body=(
                    f"Customer enquiry completed manually by "
                    f"{self.env.user.display_name}."
                ),
                subtype_xmlid="mail.mt_note",
            )

        return True

    def action_block_email(self):
        """
        Block the sender's email address and close the enquiry.

        Only the individual email address is blocked here.
        Whole-domain blocking remains a separate deliberate action.
        """

        Blocklist = self.env[
            "adi.helpdesk.blocklist"
        ].with_context(active_test=False)

        for enquiry in self:
            email = (enquiry.email or "").strip().lower()

            if not email:
                continue

            existing_block = Blocklist.search([
                ("block_type", "=", "email"),
                ("value", "=", email),
            ], limit=1)

            reason = (
                "Blocked from Customer Enquiry review."
            )

            if existing_block:
                existing_block.write({
                    "active": True,
                    "reason": reason,
                })
            else:
                Blocklist.create({
                    "block_type": "email",
                    "value": email,
                    "reason": reason,
                })

            enquiry.write({
                "state": "closed",
                "closure_reason": "blocked",
            })

            enquiry.message_post(
                body=(
                    f"Email address {email} blocked and enquiry "
                    f"closed by {self.env.user.display_name}."
                ),
                subtype_xmlid="mail.mt_note",
            )

        return True