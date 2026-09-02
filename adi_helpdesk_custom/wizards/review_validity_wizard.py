from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import email_split


class AdiHelpdeskReviewValidityWizard(models.TransientModel):
    _name = "adi.helpdesk.review.validity.wizard"
    _description = "Review Helpdesk Ticket Validity"

    ticket_id = fields.Many2one(
        "helpdesk.ticket",
        string="Ticket",
        required=True,
        readonly=True,
    )

    company_id = fields.Many2one(
        "res.partner",
        string="Company",
        domain="[('is_company', '=', True)]",
    )

    contact_name = fields.Char(
        string="Contact Name",
    )

    contact_email = fields.Char(
        string="Contact Email",
    )

    block_email = fields.Boolean(
        string="Block Email",
        default=True,
    )

    block_domain = fields.Boolean(
        string="Block Domain",
        default=True,
    )

    domain_status = fields.Selection(
        [
            ("approved", "Registered Contact Domain"),
            ("blocked", "Blocked Domain"),
            ("unknown", "Unknown Domain"),
            ("none", "No Domain"),
        ],
        string="Domain Status",
        compute="_compute_domain_status",
    )

    domain_status_message = fields.Html(
        string="Domain Check",
        compute="_compute_domain_status",
    )

    adi_suggested_company_ids = fields.Many2many(
        "res.partner",
        string="Suggested Companies",
        compute="_compute_adi_suggested_companies",
    )

    adi_block_domain_allowed = fields.Boolean(
        compute="_compute_adi_block_domain_allowed"
    )

    adi_suggested_company_names = fields.Text(
        string="Suggested Companies",
        compute="_compute_adi_suggested_companies",
    )

    adi_company_domain = fields.Char(
        string="Company Domain",
        compute="_compute_adi_suggested_companies",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        ticket = self.env["helpdesk.ticket"].browse(
            self.env.context.get("default_ticket_id")
        )

        if ticket:
            res["contact_email"] = (
                ticket.adi_submitted_email
                or ticket.partner_email
            )

            if ticket.adi_submitted_contact_name:
                res["contact_name"] = (
                    ticket.adi_submitted_contact_name
                )
            elif ticket.partner_name:
                name = ticket.partner_name.strip()

                if "@" not in name:
                    res["contact_name"] = name

        return res

    # ---------------------------------------------------------
    # Helper: derive companies from registered contact emails
    # ---------------------------------------------------------

    def _adi_companies_from_email_domain(self, email):
        """
        Return companies that already have active individual
        contacts using the same email domain.

        This is guidance only.

        A matching domain does not make the sender a trusted
        Helpdesk contact. Trust is established elsewhere using
        an exact registered contact email match.
        """

        email = (email or "").strip().lower()

        if not email or "@" not in email:
            return self.env["res.partner"]

        domain = email.rsplit("@", 1)[-1].strip()

        contacts = self.env["res.partner"].search([
            ("is_company", "=", False),
            ("active", "=", True),
            ("parent_id", "!=", False),
            ("email", "!=", False),
            ("email", "ilike", f"@{domain}"),
        ])

        matching_contacts = contacts.filtered(
            lambda contact:
                any(
                    address.strip().lower().endswith(
                        f"@{domain}"
                    )
                    for address in email_split(
                        contact.email or ""
                    )
                )
        )

        return matching_contacts.mapped(
            "commercial_partner_id"
        )

    # ---------------------------------------------------------
    # Accept validity check and move to contact review
    # ---------------------------------------------------------

    def action_accept(self):
        self.ensure_one()

        contact_email = (
            self.contact_email or ""
        ).strip().lower()

        if not contact_email or "@" not in contact_email:
            raise UserError(
                "Please enter a valid contact email address "
                "before moving to contact review."
            )

        new_stage = self.env["helpdesk.stage"].search([
            ("name", "=", "New"),
        ], limit=1)

        if not new_stage:
            raise UserError(
                "Could not find a Helpdesk stage called 'New'."
            )

        self.ticket_id.write({
            "stage_id": new_stage.id,
            "adi_submitted_email": contact_email,
            "partner_id": False,
            "partner_email": False,
            "partner_name": False,
            "adi_validity_check_required": False,
            "adi_new_contact_review_required": True,
            "adi_matched_company_id": False,
        })

        return {
            "type": "ir.actions.act_window_close",
        }

    # ---------------------------------------------------------
    # Mark ticket / sender as spam
    # ---------------------------------------------------------

    def action_mark_spam(self):
        self.ensure_one()

        if self.domain_status == "approved":
            return {
                "type": "ir.actions.act_window",
                "name": "Confirm Email Block",
                "res_model": (
                    "adi.helpdesk.confirm.email.block.wizard"
                ),
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_wizard_id": self.id,
                },
            }

        return self.action_mark_spam_confirmed()

    def action_mark_spam_confirmed(self):
        self.ensure_one()

        Blocklist = self.env[
            "adi.helpdesk.blocklist"
        ].with_context(active_test=False)

        email = (
            self.contact_email
            or self.ticket_id.adi_submitted_email
            or self.ticket_id.partner_email
        )

        email = (
            email.strip().lower()
            if email
            else False
        )

        domain = (
            email.split("@")[-1].strip()
            if email and "@" in email
            else False
        )

        reason = (
            "Marked as spam from Helpdesk validity review."
        )

        if self.block_email and email:
            existing_email_block = Blocklist.search([
                ("block_type", "=", "email"),
                ("value", "=", email),
            ], limit=1)

            if existing_email_block:
                existing_email_block.write({
                    "active": True,
                    "reason": reason,
                })
            else:
                Blocklist.create({
                    "block_type": "email",
                    "value": email,
                    "reason": reason,
                })

        # A domain already used by registered customer contacts
        # must not be blocked from this wizard.
        if (
            self.block_domain
            and domain
            and self.domain_status != "approved"
        ):
            existing_domain_block = Blocklist.search([
                ("block_type", "=", "domain"),
                ("value", "=", domain),
            ], limit=1)

            if existing_domain_block:
                existing_domain_block.write({
                    "active": True,
                    "reason": reason,
                })
            else:
                Blocklist.create({
                    "block_type": "domain",
                    "value": domain,
                    "reason": reason,
                })

        self.ticket_id.write({
            "adi_validity_check_required": False,
            "adi_new_contact_review_required": False,
            "partner_id": False,
            "active": False,
        })

        return {
            "type": "ir.actions.act_window_close",
        }

    # ---------------------------------------------------------
    # Compute domain status
    # ---------------------------------------------------------

    @api.depends("contact_email")
    def _compute_domain_status(self):
        for wizard in self:
            email = (
                wizard.contact_email
                or wizard.ticket_id.adi_submitted_email
                or wizard.ticket_id.partner_email
            )

            wizard.domain_status = "none"
            wizard.domain_status_message = (
                "No email/domain available."
            )

            if not email or "@" not in email:
                continue

            email = email.strip().lower()
            domain = email.rsplit("@", 1)[-1].strip()

            blocked_domain = wizard.env[
                "adi.helpdesk.blocklist"
            ].search([
                ("block_type", "=", "domain"),
                ("value", "=", domain),
                ("active", "=", True),
            ], limit=1)

            if blocked_domain:
                wizard.domain_status = "blocked"
                wizard.domain_status_message = (
                    f"<strong>{domain}</strong> "
                    "is already blocked."
                )
                continue

            companies = (
                wizard._adi_companies_from_email_domain(
                    email
                )
            )

            if companies:
                wizard.domain_status = "approved"
                wizard.domain_status_message = (
                    f"<strong>{domain}</strong> is used by "
                    "registered customer contacts."
                )
                continue

            wizard.domain_status = "unknown"
            wizard.domain_status_message = (
                f"<strong>{domain}</strong> is not currently "
                "used by any registered customer contact."
            )

    # ---------------------------------------------------------
    # Suggested companies based on registered contact domains
    # ---------------------------------------------------------

    @api.depends("contact_email")
    def _compute_adi_suggested_companies(self):
        for wizard in self:
            wizard.adi_suggested_company_ids = False
            wizard.adi_suggested_company_names = False
            wizard.adi_company_domain = str([
                ("id", "=", 0),
            ])

            email = (
                wizard.contact_email
                or wizard.ticket_id.adi_submitted_email
            )

            if not email or "@" not in email:
                continue

            companies = (
                wizard._adi_companies_from_email_domain(
                    email
                )
            )

            if companies:
                wizard.adi_suggested_company_ids = (
                    companies
                )

                wizard.adi_suggested_company_names = (
                    "\n\n".join(
                        companies.mapped("display_name")
                    )
                )

                wizard.adi_company_domain = str([
                    ("id", "in", companies.ids),
                    ("is_company", "=", True),
                    ("active", "=", True),
                ])

    # ---------------------------------------------------------
    # Compute whether whole-domain blocking is permitted
    # ---------------------------------------------------------

    @api.depends("domain_status")
    def _compute_adi_block_domain_allowed(self):
        for wizard in self:
            wizard.adi_block_domain_allowed = (
                wizard.domain_status != "approved"
            )

    def action_recheck_domain(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Review Validity Check",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }