from odoo import api, fields, models
from odoo.exceptions import UserError
import difflib


class AdiHelpdeskSetInProgressWizard(models.TransientModel):
    _name = "adi.helpdesk.set.in.progress.wizard"
    _description = "Set Helpdesk Ticket to In Progress"

    ticket_id = fields.Many2one(
        "helpdesk.ticket",
        string="Ticket",
        required=True,
        readonly=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Assigned to",
        required=True,
    )

    adi_new_contact_review_required = fields.Boolean(
        string="New Contact Review Required",
        related="ticket_id.adi_new_contact_review_required",
        readonly=True,
    )

    company_id = fields.Many2one(
        "res.partner",
        string="Company",
        domain="[('is_company', '=', True)]",
    )

    contact_name = fields.Char(string="Contact Name")
    contact_email = fields.Char(string="Contact Email")

    create_contact = fields.Boolean(
        string="Create Contact",
        default=True,
    )

    matched_contact_id = fields.Many2one(
        "res.partner",
        string="Matched Contact",
        readonly=True,
    )

    adi_company_domain = fields.Char(
        string="Company Domain",
        compute="_compute_adi_company_guidance",
    )

    adi_suggested_company_names = fields.Text(
        string="Suggested Companies",
        compute="_compute_adi_company_guidance",
    )

    adi_domain_status = fields.Selection(
        [
            ("approved", "Approved Customer Domain"),
            ("unknown", "Unknown Domain"),
            ("none", "No Domain"),
        ],
        string="Domain Status",
        compute="_compute_adi_company_guidance",
    )

    adi_domain_status_message = fields.Html(
        string="Domain Check",
        compute="_compute_adi_company_guidance",
    )

    adi_severity = fields.Selection(
        related="ticket_id.adi_severity",
        string="Severity",
        readonly=False,
        required=True,
    )

    adi_severity_guidance = fields.Html(
        string="Severity Guidance",
        compute="_compute_adi_severity_guidance",
        readonly=True,
    )

    adi_test_asset_name = fields.Char(
        string="Confirmed Resource(s)",
    )

    adi_customer_input_serial_number = fields.Char(
        related="ticket_id.adi_customer_input_serial_number",
        string="Customer Asset / Serial No",
        readonly=True,
    )

    adi_customer_asset_guidance = fields.Html(
        string="Customer Asset Guidance",
        compute="_compute_adi_customer_asset_guidance",
        readonly=True,
    )


    adi_charge_to_order_id = fields.Many2one(
        "sale.order",
        string="Charge to",
    )

    adi_charge_type = fields.Selection(
        [
            ("support", "Support Contract"),
            ("warranty", "Sales Order Transfer or Warranty Claim"),
            ("expense", "Expense to 78000"),
        ],
        string="Charge Method",
        required=True,
    )

    adi_charge_to_order_domain = fields.Binary(
        compute="_compute_adi_charge_to_order_domain",
    )

    adi_interested_user_ids = fields.Many2many(
        "res.users",
        string="Followers",
        domain=[
            ("active", "=", True),
            ("share", "=", False),
        ],
    )

    @api.depends(
        "ticket_id.partner_id",
        "company_id",
        "matched_contact_id",
        "adi_charge_type",
    )
    def _compute_adi_charge_to_order_domain(self):
        for wizard in self:
            company = (
                wizard.company_id
                or wizard.matched_contact_id.commercial_partner_id
                or wizard.ticket_id.partner_id.commercial_partner_id
            )

            if not company:
                wizard.adi_charge_to_order_domain = [
                    ("id", "=", 0),
                ]
                continue

            base_domain = [
                ("partner_id", "child_of", company.id),
                ("state", "=", "sale"),
            ]

            # Support Contract:
            # Maintenance / Maintenance Plus orders that are In progress.
            if wizard.adi_charge_type == "support":
                wizard.adi_charge_to_order_domain = base_domain + [
                    (
                        "x_studio_sales_order_type",
                        "in",
                        ["Maintenance", "Maintenance Plus"],
                    ),
                    (
                        "x_studio_lifecycle",
                        "=",
                        "In progress",
                    ),
                ]

            # Sales Order Transfer or Warranty Claim:
            # Any non-maintenance order whose lifecycle is either
            # In progress or Warranty.
            elif wizard.adi_charge_type == "warranty":
                wizard.adi_charge_to_order_domain = base_domain + [
                    (
                        "x_studio_sales_order_type",
                        "not in",
                        ["Maintenance", "Maintenance Plus"],
                    ),
                    (
                        "x_studio_lifecycle",
                        "in",
                        ["In progress", "Warranty"],
                    ),
                ]

            # Expense to 78000:
            # No Sales Order is selected.
            else:
                wizard.adi_charge_to_order_domain = [
                    ("id", "=", 0),
                ]

    adi_contract_date_range = fields.Char(
        string="Contract Date Range",
        readonly=True,
    )

    adi_contract_status = fields.Selection(
        [
            ("active", "In Contract"),
            ("warning", "Contract Expiring"),
            ("expired", "Out of Contract"),
            ("unknown", "Unknown"),
        ],
        string="Contract Status",
        readonly=True,
        default="unknown",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        ticket = self.env["helpdesk.ticket"].browse(
            self.env.context.get("default_ticket_id")
        )

        if not ticket:
            return res

        res["contact_email"] = ticket.adi_submitted_email or ticket.partner_email

        if ticket.adi_submitted_contact_name:
            res["contact_name"] = ticket.adi_submitted_contact_name
        elif ticket.partner_name:
            name = ticket.partner_name.strip()
            if "@" not in name:
                res["contact_name"] = name

        if ticket.adi_matched_company_id:
            res["company_id"] = ticket.adi_matched_company_id.id

        contact = self._adi_find_contact_by_email(res.get("contact_email"))

        if contact:
            res.update({
                "matched_contact_id": contact.id,
                "contact_name": contact.name,
                "company_id": contact.parent_id.id or contact.commercial_partner_id.id,
                "create_contact": False,
            })

        internal_followers = ticket.message_partner_ids.user_ids.filtered(
            lambda user:
                user.active
                and not user.share
        )

        res["adi_interested_user_ids"] = [
            (6, 0, internal_followers.ids)
        ]


        res["adi_test_asset_name"] = (
            ticket.adi_test_asset_id
            or ticket.adi_customer_input_serial_number
        )

        return res

    def action_confirm(self):
        self.ensure_one()

        if not self.user_id:
            raise UserError(
                "Please select an Assigned to user before continuing."
            )

        if not self.adi_charge_type:
            raise UserError(
                "Please select how this ticket should be charged."
            )

        if (
            self.adi_charge_type in ("support", "warranty")
            and not self.adi_charge_to_order_id
        ):
            raise UserError(
                "Please select the Sales Order this ticket should be charged to."
            )

        stage = self.env["helpdesk.stage"].search(
            [("name", "=", "In Progress")],
            limit=1,
        )

        if not stage:
            raise UserError("Could not find a Helpdesk stage called 'In Progress'.")

        values = {
            "user_id": self.user_id.id,
            "stage_id": stage.id,
            "adi_test_asset_id": self.adi_test_asset_name,
            "adi_charge_to_order_id": self.adi_charge_to_order_id.id,
            "adi_non_contract": self.adi_charge_type == "expense",
            "adi_contract_date_range": self.adi_contract_date_range,
            "adi_contract_status": dict(
                self._fields["adi_contract_status"].selection
            ).get(
                self.adi_contract_status,
                "Unknown",
            )
        }

        if self.ticket_id.adi_new_contact_review_required:
            self._adi_prepare_contact_review_values(values)

        self.ticket_id.write(values)

        if self.adi_interested_user_ids:
            self.ticket_id.message_subscribe(
                partner_ids=self.adi_interested_user_ids.partner_id.ids,
            )        

        if self.env.context.get("adi_open_ticket_after_set_in_progress"):
            return {
                "type": "ir.actions.act_window",
                "name": self.ticket_id.display_name,
                "res_model": "helpdesk.ticket",
                "res_id": self.ticket_id.id,
                "view_mode": "form",
                "target": "current",
            }

        return {"type": "ir.actions.act_window_close"}

    def action_block_sender(self):
        self.ensure_one()

        email = (
            self.contact_email
            or self.ticket_id.adi_submitted_email
            or self.ticket_id.partner_email
            or ""
        ).strip().lower()

        if not email or "@" not in email:
            raise UserError("No valid sender email is available to block.")

        block = self.env["adi.helpdesk.blocklist"].search([
            ("block_type", "=", "email"),
            ("value", "=", email),
        ], limit=1)

        if block:
            block.write({"active": True})
        else:
            self.env["adi.helpdesk.blocklist"].create({
                "block_type": "email",
                "value": email,
                "active": True,
            })

        self.ticket_id.write({
            "active": False,
            "adi_new_contact_review_required": False,
            "adi_validity_check_required": False,
        })

        return {"type": "ir.actions.act_window_close"}

    def _adi_prepare_contact_review_values(self, values):
        contact_email = (self.contact_email or "").strip().lower()

        if not contact_email or "@" not in contact_email:
            raise UserError("Please enter a valid contact email address before continuing.")

        if self.adi_domain_status != "approved":
            raise UserError(
                "This email domain is not approved for Helpdesk use. "
                "Correct the email address or return the ticket to validity review."
            )

        if self.matched_contact_id:
            contact = self.matched_contact_id
        else:
            contact = self._adi_find_contact_by_email(contact_email)

        if contact:
            self._adi_apply_existing_contact(values, contact)
            return

        if not self.company_id:
            raise UserError("Please select the correct company before continuing.")

        if not self.create_contact:
            values.update({
                "partner_id": False,
                "partner_email": False,
                "partner_name": False,
                "adi_new_contact_review_required": False,
                "adi_validity_check_required": False,
                "adi_matched_company_id": self.company_id.id,
            })
            return

        contact_name = (self.contact_name or "").strip()

        if not contact_name:
            raise UserError("Please enter the contact name before creating a new contact.")

        contact = self.env["res.partner"].create({
            "name": contact_name,
            "email": contact_email,
            "parent_id": self.company_id.id,
            "type": "contact",
            "is_company": False,
        })

        self._adi_apply_existing_contact(values, contact)

    def _adi_apply_existing_contact(self, values, contact):
        values.update({
            "partner_id": contact.id,
            "partner_email": contact.email,
            "partner_name": contact.name,
            "adi_new_contact_review_required": False,
            "adi_validity_check_required": False,
            "adi_matched_company_id": contact.commercial_partner_id.id,
        })

    def _adi_find_contact_by_email(self, email):
        email = (email or "").strip().lower()

        if not email or "@" not in email:
            return self.env["res.partner"]

        return self.env["res.partner"].search([
            ("email", "=ilike", email),
            ("active", "=", True),
            ("is_company", "=", False),
        ], limit=1)

    @api.onchange("contact_email")
    def _onchange_contact_email(self):
        self.matched_contact_id = False
        self.create_contact = True

        contact = self._adi_find_contact_by_email(self.contact_email)

        if contact:
            self.matched_contact_id = contact.id
            self.contact_name = contact.name
            self.company_id = contact.parent_id.id or contact.commercial_partner_id.id
            self.create_contact = False

    # Compute the contract date range and status based on the selected charge-to order. 
    # This is to help the agent quickly identify whether the customer is in contract, 
    # out of contract, or nearing contract expiry, so they can make informed decisions about how to handle the ticket.

    def _adi_format_date(self, date_value):
        return (
            date_value.strftime("%d %b %Y")
            if date_value
            else ""
        )

    @api.onchange("adi_charge_to_order_id")
    def _onchange_adi_charge_to_order_id(self):
        for wizard in self:
            order = wizard.adi_charge_to_order_id

            if not order:
                wizard.adi_contract_date_range = False
                wizard.adi_contract_status = "unknown"
                continue

            start_date = order.x_studio_mnt_start_of_cover_date
            end_date = order.x_studio_mnt_end_of_cover_date
            today = fields.Date.context_today(wizard)

            if start_date and end_date:
                wizard.adi_contract_date_range = (
                    f"{wizard._adi_format_date(start_date)} - "
                    f"{wizard._adi_format_date(end_date)}"
                )
            elif start_date:
                wizard.adi_contract_date_range = (
                    f"From {wizard._adi_format_date(start_date)}"
                )
            elif end_date:
                wizard.adi_contract_date_range = (
                    f"Until {wizard._adi_format_date(end_date)}"
                )
            else:
                wizard.adi_contract_date_range = (
                    "No cover dates recorded"
                )

            if start_date and today < start_date:
                wizard.adi_contract_status = "warning"
            elif end_date and today > end_date:
                wizard.adi_contract_status = "expired"
            elif end_date and (end_date - today).days <= 30:
                wizard.adi_contract_status = "warning"
            elif start_date or end_date:
                wizard.adi_contract_status = "active"
            else:
                wizard.adi_contract_status = "unknown"

    # Compute guidance and domain checks based on the email address provided by the customer to help the agent identify
    # the correct company to link to the ticket and ensure that customers from unapproved domains are flagged for review.
    @api.depends("contact_email")

    def _compute_adi_company_guidance(self):
        for wizard in self:
            email = (
                wizard.contact_email
                or wizard.ticket_id.adi_submitted_email
                or wizard.ticket_id.partner_email
            )

            wizard.adi_company_domain = str([("id", "=", 0)])
            wizard.adi_suggested_company_names = False
            wizard.adi_domain_status = "none"
            wizard.adi_domain_status_message = "No email/domain available."

            if not email or "@" not in email:
                continue

            domain = email.strip().lower().split("@")[-1]

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

            companies = wizard.env["res.partner"].search([
                ("is_company", "=", True),
                ("active", "=", True),
                ("adi_approved_helpdesk_domain", "=ilike", domain),
            ])

            if companies:
                wizard.adi_domain_status = "approved"
                wizard.adi_domain_status_message = (
                    f"<strong>{domain}</strong> is an approved customer domain."
                )
                wizard.adi_suggested_company_names = "\n\n".join(
                    companies.mapped("display_name")
                )
                wizard.adi_company_domain = str([
                    ("id", "in", companies.ids),
                    ("is_company", "=", True),
                    ("active", "=", True),
                ])
                continue

            closest_matches = difflib.get_close_matches(
                domain,
                approved_domains,
                n=1,
                cutoff=0.8,
            )

            wizard.adi_domain_status = "unknown"

            if closest_matches:
                wizard.adi_domain_status_message = (
                    f"<strong>{domain}</strong> is not listed as an approved customer domain. "
                    f"Did you mean <strong>{closest_matches[0]}</strong>?"
                )
            else:
                wizard.adi_domain_status_message = (
                    f"<strong>{domain}</strong> is not listed as an approved customer domain."
                )

    # Compute guidance for severity selection to help the agent choose the right level based on the customer's
    # description of the problem and its impact on their operations. This is to encourage consistent severity 
    # selection and ensure that high severity issues are appropriately prioritised.
    @api.depends("adi_severity")
    def _compute_adi_severity_guidance(self):
        guidance = """
            <div style="font-style: italic; color: #667085; line-height: 1.5;">
                
                <strong>High:</strong> Critical issue preventing operation or testing.<br/>
                <strong>Medium:</strong> Normal operational issue affecting workflow.<br/>
                <strong>Low:</strong> Minor issue or cosmetic problem.
            </div>
        """

        for wizard in self:
            wizard.adi_severity_guidance = guidance


    # Compute guidance based on whether the customer indicated a resource/serial number and what that number is

    @api.depends("ticket_id.adi_customer_input_serial_number")
    def _compute_adi_customer_asset_guidance(self):
        for wizard in self:
            resource = (wizard.ticket_id.adi_customer_input_serial_number or "").strip()

            if resource:
                wizard.adi_customer_asset_guidance = f"""
                    <div style="font-style: italic; color: #667085; line-height: 1.5;">
                        The customer indicated an issue with <strong>{resource}</strong>.
                    </div>
                """
            else:
                wizard.adi_customer_asset_guidance = """
                    <div style="font-style: italic; color: #667085; line-height: 1.5;">
                        * The customer did not indicate which resource the problem relates to.
                    </div>
                """        


    @api.onchange("adi_charge_type")
    def _onchange_adi_charge_type(self):
        for wizard in self:
            wizard.adi_charge_to_order_id = False
            wizard.adi_contract_date_range = False
            wizard.adi_contract_status = "unknown"   