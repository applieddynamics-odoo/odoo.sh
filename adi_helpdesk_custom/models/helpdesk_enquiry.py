from odoo import api, fields, models, tools
from markupsafe import Markup

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
    # Incoming unknown Helpdesk email
    # ---------------------------------------------------------

    @api.model
    def message_new(self, msg, custom_values=None):
        """
        Create a Customer Enquiry from an unknown NEW inbound
        Helpdesk email.

        Only the minimum information required for manager review
        is retained:

        - subject
        - sender email
        - body text

        Attachments are deliberately not retained.
        No Contact is created.
        """

        sender_addresses = tools.email_split(
            msg.get("email_from")
            or msg.get("from")
            or ""
        )

        sender_email = (
            sender_addresses[0].strip().lower()
            if sender_addresses
            else "unknown"
        )

        subject = (
            (msg.get("subject") or "").strip()
            or "Customer Enquiry"
        )

        body = msg.get("body") or ""

        message_text = (
            tools.html2plaintext(str(body)).strip()
            if body
            else ""
        )

        enquiry = self.create({
            "name": subject,
            "email": sender_email,
            "message": message_text,
            "state": "new",
        })

        # -----------------------------------------------------
        # Notify active Helpdesk Managers.
        #
        # Use the configured ADI Helpdesk identity but retain
        # Odoo's standard notification layout. This deliberately
        # avoids changing inbound mail routing or introducing a
        # dedicated email layout.
        # -----------------------------------------------------

        manager_group = self.env.ref(
            "helpdesk.group_helpdesk_manager",
            raise_if_not_found=False,
        )

        if manager_group:
            manager_partners = (
                manager_group.users.filtered(
                    lambda user: user.active
                ).partner_id
            )

            if manager_partners:
                helpdesk_team = self.env[
                    "helpdesk.team"
                ].search([
                    ("alias_id.alias_name", "=", "helpdesk"),
                ], limit=1)

                author = (
                    helpdesk_team.adi_message_author_id
                    if helpdesk_team
                    else False
                )

                notify_values = {
                    "partner_ids": manager_partners.ids,
                    "subject": f"<<Customer Enquiry>> {subject}",
                    "body": Markup(
                        "<p>"
                        "An email has been received at ADI Helpdesk "
                        "from a sender who is not a registered "
                        "Helpdesk contact."
                        "</p>"
                        f"<p><strong>From:</strong> {sender_email}</p>"
                        "<p>"
                        "Please review the Customer Enquiry record "
                        "in Helpdesk."
                        "</p>"
                    ),
                }

                if author:
                    notify_values.update({
                        "author_id": author.id,
                        "email_from": (
                            f"{helpdesk_team.name} "
                            f"<{helpdesk_team.alias_email}>"
                            if helpdesk_team.alias_email
                            else author.email_formatted
                        ),
                    })

                enquiry.with_context(
                    mail_notify_author=True,
                ).message_notify(
                    **notify_values
                )

        return enquiry

    def message_post(self, **kwargs):
        """
        Do not retain attachments arriving with unknown Helpdesk
        email.

        Odoo's mail router posts the incoming email to the newly
        created thread after message_new(). Strip attachment data
        before that happens.
        """

        if self.env.context.get("from_alias"):
            kwargs = dict(kwargs)
            kwargs.pop("attachments", None)
            kwargs.pop("attachment_ids", None)

        return super().message_post(**kwargs)

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
        Add the individual sender email to the Helpdesk blocklist
        and close the enquiry.

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