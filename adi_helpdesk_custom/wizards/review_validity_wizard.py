from odoo import api, fields, models
import difflib
from odoo.exceptions import UserError


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
            ("approved", "Approved Customer Domain"),
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
            res["contact_email"] = ticket.adi_submitted_email or ticket.partner_email

            if ticket.adi_submitted_contact_name:
                res["contact_name"] = ticket.adi_submitted_contact_name
            elif ticket.partner_name:
                name = ticket.partner_name.strip()
                if "@" not in name:
                    res["contact_name"] = name

        return res


    # -------------------------------------------------------------------------------------------------------------------------
    # ACTION TO CHECK THE DOMAIN AND MOVE THE TICKET TO CONTACT REVIEW STAGE FOR MANUAL REVIEW OF THE CONTACT DETAILS
    # -------------------------------------------------------------------------------------------------------------------------


    def action_accept(self):
        self.ensure_one()

        contact_email = (self.contact_email or "").strip().lower()

        if not contact_email or "@" not in contact_email:
            raise UserError("Please enter a valid contact email address before moving to contact review.")

        domain = contact_email.split("@")[-1].strip()

        approved_domain = self.env["res.partner"].search([
            ("is_company", "=", True),
            ("active", "=", True),
            ("adi_approved_helpdesk_domain", "=ilike", domain),
        ], limit=1)

        if not approved_domain:
            raise UserError("This domain is still not approved. Correct the email domain or mark the ticket as spam.")

        new_stage = self.env["helpdesk.stage"].search([
            ("name", "=", "New")
        ], limit=1)

        if not new_stage:
            raise UserError("Could not find a Helpdesk stage called 'New'.")

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

        return {"type": "ir.actions.act_window_close"}
    # -------------------------------------------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------------------------------------------

    def action_mark_spam(self):
        self.ensure_one()

        if self.domain_status == "approved":
            return {
                "type": "ir.actions.act_window",
                "name": "Confirm Email Block",
                "res_model": "adi.helpdesk.confirm.email.block.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_wizard_id": self.id,
                },
            }

        return self.action_mark_spam_confirmed()

    def action_mark_spam_confirmed(self):
        self.ensure_one()

        Blocklist = self.env["adi.helpdesk.blocklist"].with_context(active_test=False)

        email = self.contact_email or self.ticket_id.adi_submitted_email or self.ticket_id.partner_email
        email = email.strip().lower() if email else False
        domain = email.split("@")[-1].strip() if email and "@" in email else False

        reason = "Marked as spam from Helpdesk validity review."

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

        if self.block_domain and domain and self.domain_status != "approved":
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

        return {"type": "ir.actions.act_window_close"}

    # -------------------------------------------------------------------------------------------------------------------------
    # COMPUTE THE DOMAIN STATUS OF THE SUBMITTED EMAIL TO DETERMINE WHETHER IT IS APPROVED, BLOCKED, UNKNOWN, OR NONE
    # -------------------------------------------------------------------------------------------------------------------------

    @api.depends("contact_email")
    def _compute_domain_status(self):
        for wizard in self:
            email = wizard.contact_email or wizard.ticket_id.adi_submitted_email or wizard.ticket_id.partner_email

            wizard.domain_status = "none"
            wizard.domain_status_message = "No email/domain available."

            if not email or "@" not in email:
                continue

            domain = email.strip().lower().split("@")[-1]

            blocked_domain = wizard.env["adi.helpdesk.blocklist"].search([
                ("block_type", "=", "domain"),
                ("value", "=", domain),
                ("active", "=", True),
            ], limit=1)

            if blocked_domain:
                wizard.domain_status = "blocked"
                wizard.domain_status_message = (
                    f"<strong>{domain}</strong> is already blocked."
                )
                continue

            approved_domain = wizard.env["res.partner"].search([
                ("is_company", "=", True),
                ("active", "=", True),
                ("adi_approved_helpdesk_domain", "=ilike", domain),
            ], limit=1)

            if approved_domain:
                wizard.domain_status = "approved"
                wizard.domain_status_message = (
                    f"<strong>{domain}</strong> is an approved customer domain."
                )
                continue

            approved_domains = wizard.env["res.partner"].search([
                ("is_company", "=", True),
                ("active", "=", True),
                ("adi_approved_helpdesk_domain", "!=", False),
            ]).mapped("adi_approved_helpdesk_domain")

            approved_domains = [
                approved_domain.strip().lower()
                for approved_domain in approved_domains
                if approved_domain
            ]

            closest_matches = difflib.get_close_matches(
                domain,
                approved_domains,
                n=1,
                cutoff=0.8,
            )

            wizard.domain_status = "unknown"

            if closest_matches:
                wizard.domain_status_message = (
                    f"<strong>{domain}</strong> is not listed as an approved customer domain. "
                    f"Did you mean <strong>{closest_matches[0]}</strong>?"
                )
            else:
                wizard.domain_status_message = (
                    f"<strong>{domain}</strong> is not listed as an approved customer domain."
                )
    # -------------------------------------------------------------------------------------------------------------------------
    # COMPUTE SUGGESTED COMPANIES BASED ON THE SUBMITTED EMAIL DOMAIN
    # -------------------------------------------------------------------------------------------------------------------------

    @api.depends("contact_email")
    def _compute_adi_suggested_companies(self):
        for wizard in self:
            wizard.adi_suggested_company_ids = False
            wizard.adi_suggested_company_names = False
            wizard.adi_company_domain = str([
                ("id", "=", 0),
            ])

            email = wizard.contact_email or wizard.ticket_id.adi_submitted_email

            if not email or "@" not in email:
                continue

            domain = email.strip().lower().split("@")[-1]

            companies = wizard.env["res.partner"].search([
                ("is_company", "=", True),
                ("active", "=", True),
                ("adi_approved_helpdesk_domain", "=ilike", domain),
            ])

            if companies:
                wizard.adi_suggested_company_ids = companies
                wizard.adi_suggested_company_names = "\n\n".join(
                    companies.mapped("display_name")
                )
                wizard.adi_company_domain = str([
                    ("id", "in", companies.ids),
                    ("is_company", "=", True),
                    ("active", "=", True),
                ])

    # -------------------------------------------------------------------------------------------------------------------------
    # COMPUTE WHETHER DOMAIN BLOCKING IS ALLOWED BASED ON THE DOMAIN STATUS 
    # -------------------------------------------------------------------------------------------------------------------------

    @api.depends("domain_status")
    def _compute_adi_block_domain_allowed(self):
        for wizard in self:
            wizard.adi_block_domain_allowed = wizard.domain_status != "approved"

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