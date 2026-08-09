from odoo import api, fields, models
from odoo.tools import email_split
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    adi_create_date_only = fields.Date(
        string="Created",
        compute="_compute_adi_create_date_only",
    )

    @api.depends("create_date")
    def _compute_adi_create_date_only(self):
        for ticket in self:
            ticket.adi_create_date_only = ticket.create_date.date() if ticket.create_date else False    
    
    
    adi_severity = fields.Selection(
        [("Low", "Low"), ("Medium", "Medium"), ("High", "High")],
        string="Severity",
    )


    adi_sir_warranty_or_maintenance_order_id = fields.Many2one(
        "sale.order",
        string="SIR Warranty or Maintenance Order",
    )

    adi_software_version_id = fields.Many2one(
        "adi.helpdesk.software.version",
        string="Software Version",
    )

    adi_spr_number = fields.Char(string="ADI SPR Number")

    adi_sir_hardware_part_number_ids = fields.Many2many(
        "product.product",
        string="SIR Hardware Part Numbers",
    )

    adi_submitted_email = fields.Char(string="Submitted Email", copy=False)
    adi_submitted_contact_name = fields.Char(string="Submitted Contact Name", copy=False)
    adi_submitted_company_name = fields.Char(string="Submitted Company Name", copy=False)

    adi_customer_company = fields.Char(
        string="Customer Company",
        related="partner_id.parent_id.name",
        store=True,
        readonly=True,
    )

    adi_customer_contact_name = fields.Char(
        related="partner_id.name",
        string="Customer",
        store=True,
    )

    adi_customer_reference_number = fields.Char(
        string="Customer Reference Number",
        default="None",
        help="This is for the customer's SIR number, if applicable.",
    )

    adi_customer_input_serial_number = fields.Char(
        string="Resource where the problem was first identified",
        help=(
            "The customer’s free-text description of the resource where "
            "the problem was first identified."
        ),
    )

    adi_customer_resource_scope = fields.Selection(
        [
            ("single", "One specific resource"),
            ("multiple", "Multiple resources"),
            ("software", "Software only issue"),
            ("unknown", "Not sure /not applicable"),
        ],
        string="Customer Reported Resource Impact",
        copy=False,
)


    adi_customer_input_sales_or_maintenance_order = fields.Char(
        string="Sales or Maintenance Order",
        help="This is what is submitted through the website form by the customer.",
        readonly=True,
    )

    adi_internal_notes = fields.Text(string="Internal Notes")

    adi_validity_check_required = fields.Boolean(
        string="Validity Check Required",
        readonly=True,
        copy=False,
    )

    adi_new_contact_review_required = fields.Boolean(
        string="New Contact Review Required",
        readonly=True,
        copy=False,
    )

    adi_matched_company_id = fields.Many2one(
        "res.partner",
        string="Matched Company",
        readonly=True,
        copy=False,
    )

    adi_can_repeat_validity = fields.Boolean(
        compute="_compute_adi_can_repeat",
    )

    adi_show_set_in_progress_button = fields.Boolean(
        compute="_compute_adi_show_set_in_progress_button",
    )

    adi_stage_entered_date = fields.Datetime(
        string="Stage Entered",
        copy=False,
    )

    adi_ticket_age_label = fields.Char(
        string="Open Age",
        compute="_compute_adi_ticket_kpi_labels",
    )

    adi_stage_age_label = fields.Char(
        string="Stage Age",
        compute="_compute_adi_ticket_kpi_labels",
    )

    adi_sla_status_label = fields.Char(
        string="SLA",
        compute="_compute_adi_ticket_kpi_labels",
    )

    adi_test_asset_id = fields.Char(
        string="Confirmed Resource(s)",
    )

    adi_non_contract = fields.Boolean(
        string="Non-contract Support",
        default=False,
    )


    adi_charge_to_order_id = fields.Many2one(
        "sale.order",
        string="Charge to",
    )

    adi_charge_to_order_domain = fields.Binary(
        compute="_compute_adi_charge_to_order_domain",
    )

    @api.depends(
        "partner_id",
        "adi_matched_company_id",
    )
    def _compute_adi_charge_to_order_domain(self):
        for ticket in self:
            company = (
                ticket.adi_matched_company_id
                or ticket.partner_id.commercial_partner_id
            )

            if not company:
                ticket.adi_charge_to_order_domain = [
                    ("id", "=", 0),
                ]
                continue

            ticket.adi_charge_to_order_domain = [
                ("partner_id", "child_of", company.id),
                ("state", "=", "sale"),
                "|",
                (
                    "x_studio_lifecycle",
                    "=",
                    "Warranty",
                ),
                "&",
                (
                    "x_studio_lifecycle",
                    "=",
                    "In progress",
                ),
                (
                    "x_studio_sales_order_type",
                    "in",
                    ["Maintenance", "Maintenance Plus"],
                ),
            ]


    def _adi_format_contract_date(self, date_value):
        return (
            date_value.strftime("%d %b %Y")
            if date_value
            else ""
        )


    def _adi_update_contract_details(self):
        for ticket in self:
            order = ticket.adi_charge_to_order_id

            if not order:
                ticket.adi_contract_date_range = False
                ticket.adi_contract_status = "Unknown"
                continue

            start_date = order.x_studio_mnt_start_of_cover_date
            end_date = order.x_studio_mnt_end_of_cover_date
            today = fields.Date.context_today(ticket)

            if start_date and end_date:
                ticket.adi_contract_date_range = (
                    f"{ticket._adi_format_contract_date(start_date)} - "
                    f"{ticket._adi_format_contract_date(end_date)}"
                )
            elif start_date:
                ticket.adi_contract_date_range = (
                    f"From {ticket._adi_format_contract_date(start_date)}"
                )
            elif end_date:
                ticket.adi_contract_date_range = (
                    f"Until {ticket._adi_format_contract_date(end_date)}"
                )
            else:
                ticket.adi_contract_date_range = (
                    "No cover dates recorded"
                )

            if start_date and today < start_date:
                ticket.adi_contract_status = "Contract Expiring"
            elif end_date and today > end_date:
                ticket.adi_contract_status = "Out of Contract"
            elif end_date and (end_date - today).days <= 30:
                ticket.adi_contract_status = "Contract Expiring"
            elif start_date or end_date:
                ticket.adi_contract_status = "In Contract"
            else:
                ticket.adi_contract_status = "Unknown"


    @api.onchange("adi_charge_to_order_id")
    def _onchange_adi_charge_to_order_id(self):
        self._adi_update_contract_details()


    def write(self, vals):
        result = super().write(vals)

        if "adi_charge_to_order_id" in vals:
            self._adi_update_contract_details()

            for ticket in self:
                super(HelpdeskTicket, ticket).write({
                    "adi_contract_date_range":
                        ticket.adi_contract_date_range,
                    "adi_contract_status":
                        ticket.adi_contract_status,
                })

        return result


    adi_contract_date_range = fields.Char(
        string="Contract Date Range",
        readonly=True,
    )

    adi_contract_status = fields.Char(
        string="Contract Status",
        readonly=True,
    )

    adi_closure_statement = fields.Text(
        string="Closure Statement",
        copy=False,
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
        copy=False,
    )

    adi_interested_user_ids = fields.Many2many(
        "res.users",
        string="Followers",
        compute="_compute_adi_interested_user_ids",
        inverse="_inverse_adi_interested_user_ids",
    )


    @api.model_create_multi
    def create(self, vals_list):
        now = fields.Datetime.now()

        if self.env.context.get("adi_internal_ticket_create"):
            for vals in vals_list:
                vals.setdefault("adi_stage_entered_date", now)
            return super().create(vals_list)

        validity_check_stage = self.env["helpdesk.stage"].search(
            [("name", "=", "Validity Check")],
            limit=1,
        )
        new_stage = self.env["helpdesk.stage"].search(
            [("name", "=", "New")],
            limit=1,
        )

        prepared_vals_list = []
        routing_results = []

        for vals in vals_list:
            vals = dict(vals)
            vals.setdefault("adi_stage_entered_date", now)

            submitted_email = vals.get("adi_submitted_email") or vals.get("partner_email")
            submitted_contact_name = vals.get("adi_submitted_contact_name") or vals.get("partner_name")
            submitted_company_name = vals.get("adi_submitted_company_name") or vals.get("partner_company_name")

            if submitted_contact_name:
                submitted_contact_name = submitted_contact_name.strip()
                if "@" not in submitted_contact_name:
                    vals["adi_submitted_contact_name"] = submitted_contact_name

            if submitted_company_name:
                vals["adi_submitted_company_name"] = submitted_company_name.strip()

            if submitted_email:
                parsed_emails = email_split(submitted_email)
                submitted_email = (
                    parsed_emails[0].strip().lower()
                    if parsed_emails
                    else False
                )
            else:
                submitted_email = False

            vals["adi_submitted_email"] = submitted_email or False

            vals["partner_id"] = False
            vals["partner_email"] = False
            vals["partner_name"] = False

            routing = {
                "email": submitted_email,
                "blocked": False,
                "trusted_contact_id": False,
                "approved_domain": False,
            }

            if submitted_email and "@" in submitted_email:
                domain = submitted_email.split("@")[-1].strip()

                blocked_email = self.env["adi.helpdesk.blocklist"].search([
                    ("block_type", "=", "email"),
                    ("value", "=", submitted_email),
                    ("active", "=", True),
                ], limit=1)

                blocked_domain = self.env["adi.helpdesk.blocklist"].search([
                    ("block_type", "=", "domain"),
                    ("value", "=", domain),
                    ("active", "=", True),
                ], limit=1)

                if blocked_email or blocked_domain:
                    routing["blocked"] = True
                else:
                    existing_contact = self.env["res.partner"].search([
                        ("email", "=ilike", submitted_email),
                        ("active", "=", True),
                    ], limit=1)

                    if existing_contact:
                        commercial_partner = existing_contact.commercial_partner_id
                        approved_domain = (
                            commercial_partner.adi_approved_helpdesk_domain
                            and commercial_partner.adi_approved_helpdesk_domain.strip().lower() == domain
                        )
                        commercial_partner = existing_contact.commercial_partner_id

                        approved_domain = (
                            commercial_partner.is_company
                            and commercial_partner.adi_approved_helpdesk_domain
                            and commercial_partner.adi_approved_helpdesk_domain.strip().lower() == domain
                        )

                        trusted_contact = bool(
                            existing_contact.parent_id
                            and commercial_partner.is_company
                            and approved_domain
                        )

                        if trusted_contact:
                            routing["trusted_contact_id"] = existing_contact.id

                    if not routing["trusted_contact_id"]:
                        matched_company = self.env["res.partner"].search([
                            ("is_company", "=", True),
                            ("active", "=", True),
                            ("adi_approved_helpdesk_domain", "=ilike", domain),
                        ], limit=1)

                        if matched_company:
                            routing["approved_domain"] = True

            prepared_vals_list.append(vals)
            routing_results.append(routing)

        tickets = super().create(prepared_vals_list)

        for ticket, routing in zip(tickets, routing_results):
            submitted_email = routing.get("email")

            if routing["blocked"]:
                ticket.write({
                    "partner_id": False,
                    "partner_email": False,
                    "partner_name": False,
                    "adi_validity_check_required": False,
                    "adi_new_contact_review_required": False,
                    "active": False,
                })
                continue

            if routing["trusted_contact_id"]:
                contact = self.env["res.partner"].browse(routing["trusted_contact_id"])
                values = {
                    "partner_id": contact.id,
                    "partner_email": submitted_email,
                    "adi_validity_check_required": False,
                    "adi_new_contact_review_required": False,
                    "adi_matched_company_id": contact.commercial_partner_id.id,
                }
                if new_stage:
                    values["stage_id"] = new_stage.id
                ticket.write(values)
                continue

            if routing["approved_domain"]:
                values = {
                    "partner_id": False,
                    "partner_email": False,
                    "partner_name": False,
                    "adi_validity_check_required": False,
                    "adi_new_contact_review_required": True,
                    "adi_matched_company_id": False,
                }
                if new_stage:
                    values["stage_id"] = new_stage.id
                ticket.write(values)
                continue

            if validity_check_stage:
                ticket.write({
                    "stage_id": validity_check_stage.id,
                    "adi_validity_check_required": True,
                    "adi_new_contact_review_required": False,
                    "partner_id": False,
                    "partner_email": False,
                    "partner_name": False,
                })

        return tickets

    def write(self, vals):
        if "stage_id" in vals:
            vals["adi_stage_entered_date"] = fields.Datetime.now()

        return super().write(vals)

    def _compute_adi_can_repeat(self):
        for rec in self:
            rec.adi_can_repeat_validity = not rec.active and not rec.partner_id

    @api.depends("stage_id")
    def _compute_adi_show_set_in_progress_button(self):
        for ticket in self:
            ticket.adi_show_set_in_progress_button = ticket.stage_id.name == "New"

    def action_adi_open_set_in_progress_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Set to In Process - {self.ticket_ref or self.display_name}",
            "res_model": "adi.helpdesk.set.in.progress.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_ticket_id": self.id,
                "default_user_id": self.user_id.id,
            },
        }

    def action_adi_open_review_validity_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Review Validity Check",
            "res_model": "adi.helpdesk.review.validity.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_ticket_id": self.id,
                "default_user_id": self.user_id.id,
            },
        }

    def action_adi_send_back_to_validity_check(self):
        validity_check_stage = self.env["helpdesk.stage"].search(
            [("name", "=", "Validity Check")],
            limit=1,
        )

        if not validity_check_stage:
            return True

        for ticket in self:
            ticket.write({
                "active": True,
                "stage_id": validity_check_stage.id,
                "adi_validity_check_required": True,
                "adi_new_contact_review_required": False,
                "adi_matched_company_id": False,
                "partner_id": False,
            })

        return True

    @api.depends("ticket_ref", "name")
    def _compute_display_name(self):
        for ticket in self:
            ticket.display_name = ticket.ticket_ref or ticket.name or ""

    def _adi_email_subject(self, email_type=None):
        """Return the standard ADI Helpdesk email subject."""

        self.ensure_one()

        subject = f"[{self.ticket_ref}] : {self.name}"

        if email_type:
            subject += f" <{email_type}>"

        return subject

    def _notify_by_email_get_base_mail_values(
        self,
        message,
        additional_values=None,
    ):
        values = super()._notify_by_email_get_base_mail_values(
            message,
            additional_values=additional_values,
        )

        self.ensure_one()

        template_subject = (
            (additional_values or {}).get("subject") or ""
        ).strip()

        message_body = str(message.body or "")

        # Odoo loses the rating template subject before this method is reached,
        # so identify rating requests from their unique rating content.

        is_rating_request = (
            message.message_type == "auto_comment"
            and "/rate/" in message_body
            and "rating/static/src/img/rating_" in message_body
        )

        is_closure_email = (
            message.message_type == "comment"
            and "<strong>Ticket Closed" in message_body
        )

        if is_rating_request:
            values["subject"] = self._adi_email_subject("Support Rating")
        elif is_closure_email:
            values["subject"] = self._adi_email_subject("Closure")
        elif template_subject:
            values["subject"] = self._adi_email_subject(template_subject)
        else:
            values["subject"] = self._adi_email_subject()

        return values

    def _track_template(self, changes):
        res = super()._track_template(changes)

        if "stage_id" not in res:
            return res

        template, mail_values = res["stage_id"]

        rating_template = self.env.ref(
            "helpdesk.rating_ticket_request_email_template",
            raise_if_not_found=False,
        )

        if not rating_template or template != rating_template:
            return res

        ticket = self[0]
        team = ticket.team_id
        author = team.adi_message_author_id

        if not author:
            return res

        mail_values = dict(mail_values)

        mail_values.update({
            "author_id": author.id,
            "email_from": (
                f"{team.name} <{team.alias_email}>"
                if team.alias_email
                else author.email_formatted
            ),
        })

        res["stage_id"] = (template, mail_values)

        return res


    def message_post_with_source(self, source_ref, *args, **kwargs):
        """Set automated Helpdesk identities and simplify rating chatter."""

        new_ticket_template = self.env.ref(
            "helpdesk.new_ticket_request_email_template",
            raise_if_not_found=False,
        )

        is_new_ticket_template = (
            new_ticket_template
            and getattr(source_ref, "_name", False) == "mail.template"
            and source_ref.id == new_ticket_template.id
        )

        if is_new_ticket_template and len(self) == 1:
            ticket = self[0]
            team = ticket.team_id
            author = team.adi_message_author_id

            if author:
                kwargs = dict(kwargs)

                kwargs.update({
                    "author_id": author.id,
                    "email_from": (
                        f"{team.name} <{team.alias_email}>"
                        if team.alias_email
                        else author.email_formatted
                    ),
                })

        messages = super().message_post_with_source(
            source_ref,
            *args,
            **kwargs,
        )

        rating_template = self.env.ref(
            "helpdesk.rating_ticket_request_email_template",
            raise_if_not_found=False,
        )

        is_helpdesk_rating_template = (
            rating_template
            and getattr(source_ref, "_name", False) == "mail.template"
            and source_ref.id == rating_template.id
        )

        if is_helpdesk_rating_template and messages:
            ticket_messages = messages.filtered(
                lambda message:
                    message.model == self._name
                    and message.res_id in self.ids
            )

            for message in ticket_messages:
                ticket = self.browse(message.res_id)

            message.write({
                "message_type": "comment",
                "subtype_id": self.env.ref("mail.mt_comment").id,
                "subject": ticket._adi_email_subject("Support Rating"),
                "body": """
                    <div style="
                        background-color: #d9f0dc;
                        border: 1px solid #9ec7a5;
                        border-radius: 8px;
                        padding: 12px 16px;
                    ">
                        <p style="margin: 0 0 6px 0;">
                            <strong>Support Rating Invitation Sent</strong>
                        </p>
                        <p style="margin: 0;">
                            Customer feedback requested.
                        </p>
                    </div>
                """,
            })

        return messages

    @api.constrains("name")
    def _check_subject_length(self):
        for record in self:
            if record.name and len(record.name) > 120:
                raise ValidationError("Subject must not exceed 120 characters.")

    def _adi_format_duration(self, delta):
        days = delta.days
        hours = delta.seconds // 3600

        if days and hours:
            return f"{days}d {hours}h"
        if days:
            return f"{days}d"
        return f"{hours}h"

    @api.depends("create_date", "adi_stage_entered_date", "sla_status_ids", "sla_deadline")
    def _compute_adi_ticket_kpi_labels(self):
        now = fields.Datetime.now()

        for ticket in self:
            ticket.adi_ticket_age_label = "Not set"
            ticket.adi_stage_age_label = "Not set"
            ticket.adi_sla_status_label = "Not set"

            if ticket.create_date:
                ticket.adi_ticket_age_label = ticket._adi_format_duration(
                    now - ticket.create_date
                )

            stage_date = ticket.adi_stage_entered_date or ticket.create_date
            if stage_date:
                ticket.adi_stage_age_label = ticket._adi_format_duration(
                    now - stage_date
                )

            if ticket.sla_status_ids:
                ticket.adi_sla_status_label = "Active"
            else:
                ticket.adi_sla_status_label = "No SLA"



    
    adi_show_close_button = fields.Boolean(
        compute="_compute_adi_show_close_button",
    )

    @api.depends("stage_id")
    def _compute_adi_show_close_button(self):
        for ticket in self:
            ticket.adi_show_close_button = ticket.stage_id.name == "In Progress"    

    def action_adi_open_close_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.ticket_ref or self.display_name} - Closure",
            "res_model": "adi.helpdesk.close.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_ticket_id": self.id,
            },
        }            

    @api.depends("message_partner_ids")
    def _compute_adi_interested_user_ids(self):
        internal_users = self.env["res.users"].search([
            ("active", "=", True),
            ("share", "=", False),
        ])

        user_by_partner = {
            user.partner_id.id: user
            for user in internal_users
        }

        for ticket in self:
            ticket.adi_interested_user_ids = self.env["res.users"].browse([
                user_by_partner[partner.id].id
                for partner in ticket.message_partner_ids
                if partner.id in user_by_partner
            ])


    def _inverse_adi_interested_user_ids(self):
        internal_users = self.env["res.users"].search([
            ("active", "=", True),
            ("share", "=", False),
        ])

        internal_partner_ids = set(
            internal_users.partner_id.ids
        )

        for ticket in self:
            selected_partner_ids = set(
                ticket.adi_interested_user_ids.partner_id.ids
            )

            current_internal_partner_ids = set(
                ticket.message_partner_ids.ids
            ) & internal_partner_ids

            partner_ids_to_add = (
                selected_partner_ids
                - current_internal_partner_ids
            )

            partner_ids_to_remove = (
                current_internal_partner_ids
                - selected_partner_ids
            )

            if partner_ids_to_add:
                ticket.message_subscribe(
                    partner_ids=list(partner_ids_to_add),
                )

            if partner_ids_to_remove:
                ticket.message_unsubscribe(
                    partner_ids=list(partner_ids_to_remove),
                )             

        