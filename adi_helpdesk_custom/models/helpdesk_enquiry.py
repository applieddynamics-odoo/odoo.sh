from odoo import fields, models


class AdiHelpdeskEnquiry(models.Model):
    _name = "adi.helpdesk.enquiry"
    _description = "Helpdesk Customer Enquiry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Subject",
        required=True,
        readonly=True,
    )

    email = fields.Char(
        string="Email",
        required=True,
        readonly=True,
    )

    message = fields.Text(
        string="Message",
        readonly=True,
    )

    state = fields.Selection(
        [
            ("new", "New"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="new",
        required=True,
        readonly=True,
        copy=False,
    )

    closure_reason = fields.Selection(
        [
            ("completed", "Completed"),
            ("blocked", "Email Blocked"),
        ],
        string="Closure Reason",
        readonly=True,
        copy=False,
    )

    closed_by_id = fields.Many2one(
        "res.users",
        string="Closed By",
        readonly=True,
        copy=False,
    )

    closed_at = fields.Datetime(
        string="Closed",
        readonly=True,
        copy=False,
    )

    # ---------------------------------------------------------
    # Complete enquiry
    # ---------------------------------------------------------

    def action_open_complete_wizard(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Complete Customer Enquiry",
            "res_model": "adi.helpdesk.enquiry.complete.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_enquiry_id": self.id,
            },
        }

    def action_complete_confirmed(self):
        """
        Close the enquiry after the manager confirms that any
        required manual actions have been completed.
        """

        for enquiry in self:
            enquiry.write({
                "state": "closed",
                "closure_reason": "completed",
                "closed_by_id": self.env.user.id,
                "closed_at": fields.Datetime.now(),
            })

        return True

    # ---------------------------------------------------------
    # Block sender email
    # ---------------------------------------------------------

    def action_block_email(self):
        """
        Add the individual sender email to the existing Helpdesk
        blocklist and close the enquiry.

        Whole-domain blocking is deliberately not performed here.
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

            reason = "Blocked from Customer Enquiry review."

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
                "closed_by_id": self.env.user.id,
                "closed_at": fields.Datetime.now(),
            })

        return True