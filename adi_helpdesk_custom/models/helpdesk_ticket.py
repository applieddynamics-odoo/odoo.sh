from odoo import api, fields, models
from odoo.tools import email_split
from odoo.exceptions import ValidationError
from markupsafe import Markup, escape
from lxml import etree
import lxml.html
from email.utils import parseaddr, formataddr


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

    adi_notification_company_name = fields.Char(
        compute="_compute_adi_notification_contact",
    )

    adi_notification_contact_name = fields.Char(
        compute="_compute_adi_notification_contact",
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
                (
                    "x_studio_lifecycle",
                    "in",
                    ["In progress", "Warranty"],
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

            order_type = (
                order.x_studio_sales_order_type or ""
            ).strip()

            is_support_contract = order_type in (
                "Maintenance",
                "Maintenance Plus",
            )

            # -------------------------------------------------
            # Normal Sales Order / Warranty allocation
            # -------------------------------------------------
            if not is_support_contract:
                ticket.adi_contract_date_range = False
                ticket.adi_contract_status = "Sales Order"
                continue

            # -------------------------------------------------
            # Maintenance support contract
            # -------------------------------------------------
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


    def _adi_helpdesk_allowed_customer_companies(self, contact):
        """
        Return the customer companies that a recognised Helpdesk
        contact is authorised to raise tickets for.

        Normal contact:
            parent company only.

        Helpdesk Partner contact:
            Partner itself, where approved, plus the active approved
            customer companies linked to that Partner.
        """

        Partner = self.env["res.partner"]

        if not contact or not contact.parent_id:
            return Partner

        parent_company = contact.parent_id

        if not parent_company.adi_helpdesk_partner:
            return parent_company

        allowed_companies = Partner

        if (
            parent_company.active
            and parent_company.adi_helpdesk_approved_company
        ):
            allowed_companies |= parent_company

        allowed_companies |= (
            parent_company
            .adi_helpdesk_customer_company_ids
            .filtered(
                lambda company:
                    company.active
                    and company.is_company
                    and company.adi_helpdesk_approved_company
            )
        )

        return allowed_companies

    @api.model_create_multi
    def create(self, vals_list):
        now = fields.Datetime.now()

        if self.env.context.get("adi_internal_ticket_create"):
            for vals in vals_list:
                vals.setdefault("adi_stage_entered_date", now)
            return super().create(vals_list)


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
            }

            if submitted_email and "@" in submitted_email:
                blocked_email = self.env["adi.helpdesk.blocklist"].search([
                    ("block_type", "=", "email"),
                    ("value", "=", submitted_email),
                ], limit=1)

                if blocked_email:
                    routing["blocked"] = True
                else:
                    existing_contact = self.env["res.partner"].search([
                        ("email", "=ilike", submitted_email),
                        ("active", "=", True),
                        ("is_company", "=", False),
                        ("parent_id", "!=", False),
                    ], limit=1)

                    if existing_contact:
                        routing["trusted_contact_id"] = existing_contact.id


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
                    "adi_new_contact_review_required": False,
                    "active": False,
                })
                continue

            if routing["trusted_contact_id"]:
                contact = self.env["res.partner"].browse(
                    routing["trusted_contact_id"]
                )

                allowed_companies = (
                    self._adi_helpdesk_allowed_customer_companies(contact)
                )

                values = {
                    "partner_id": contact.id,
                    "partner_email": submitted_email,
                    "adi_new_contact_review_required": False,
                }

                # Where there is exactly one possible customer company,
                # resolve it immediately.
                #
                # Where a Helpdesk Partner contact can act for several
                # companies, leave the customer unresolved until the
                # Set In Progress wizard.
                if len(allowed_companies) == 1:
                    values["adi_matched_company_id"] = allowed_companies.id
                else:
                    values["adi_matched_company_id"] = False

                if new_stage:
                    values["stage_id"] = new_stage.id

                ticket.write(values)
                continue

        return tickets

    def write(self, vals):
        vals = dict(vals)

        # Remember Lead before the write so we can detect a genuine
        # assignment or reassignment afterwards.
        previous_user_ids = {
            ticket.id: ticket.user_id.id
            for ticket in self
        }

        # Maintain the date on which the ticket entered its current stage.
        if "stage_id" in vals:
            vals["adi_stage_entered_date"] = fields.Datetime.now()

        result = super().write(vals)

        # Maintain the displayed contract information whenever the
        # Charge To order changes.
        if "adi_charge_to_order_id" in vals:
            self._adi_update_contract_details()

            for ticket in self:
                super(HelpdeskTicket, ticket).write({
                    "adi_contract_date_range": ticket.adi_contract_date_range,
                    "adi_contract_status": ticket.adi_contract_status,
                })

        # Detect Lead assignment/reassignment.
        #
        # For the moment this only establishes the correct central hook.
        # We will add the assignment email here once we've confirmed the
        # exact mail mechanism we want to use.
        if "user_id" in vals:
            for ticket in self:
                previous_user_id = previous_user_ids.get(ticket.id)
                new_user = ticket.user_id

                if not new_user or new_user.id == previous_user_id:
                    continue

                team = ticket.team_id
                author = team.adi_message_author_id

                notify_values = {
                    "partner_ids": [new_user.partner_id.id],

                    "subject": (
                        f"<<Lead Assigned>> "
                        f"{ticket._adi_email_subject()}"
                    ),
                    "body": "",
                    "email_layout_xmlid": (
                        "adi_helpdesk_custom."
                        "adi_helpdesk_new_ticket_notification"
                    ),
                }

                if author:
                    notify_values.update({
                        "author_id": author.id,
                        "email_from": (
                            f"{team.name} <{team.alias_email}>"
                            if team.alias_email
                            else author.email_formatted
                        ),
                    })

                ticket.with_context(
                    mail_notify_author=True,
                ).message_notify(
                    **notify_values
                )

        return result
    

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

        # ---------------------------------------------------------
        # Helpdesk redistributed message identity
        # ---------------------------------------------------------
        #
        # Human-authored Helpdesk messages may originate from:
        # - incoming email
        # - internal chatter
        # - customer portal
        #
        # When Odoo redistributes those messages by email, retain
        # the real author name but make it clear that delivery was
        # through ADI Helpdesk.
        # ---------------------------------------------------------

        helpdesk_author = self.team_id.adi_message_author_id

        if (
            message.message_type in ("email", "comment")
            and message.author_id
            and message.author_id != helpdesk_author
        ):
            sender_name = (
                f"{message.author_id.name} via ADI Helpdesk"
            )

            _current_name, sender_email = parseaddr(
                values.get("email_from")
                or message.email_from
                or ""
            )

            if sender_email:
                values["email_from"] = formataddr(
                    (sender_name, sender_email)
                )

        template_subject = (
            (additional_values or {}).get("subject") or ""
        ).strip()

        message_body = str(message.body or "")

        # ---------------------------------------------------------
        # New ticket notification
        #
        # The automatic Helpdesk creation notification uses
        # helpdesk.mt_ticket_new.
        #
        # Only this notification receives the [New SIR Ticket]
        # prefix so managers can reliably identify / filter it.
        # ---------------------------------------------------------

        ticket_created_subtype = self.env.ref(
            "helpdesk.mt_ticket_new",
            raise_if_not_found=False,
        )

        is_new_ticket = bool(
            ticket_created_subtype
            and message.subtype_id == ticket_created_subtype
        )

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

        is_lead_assignment = (
            message.subject
            and message.subject.startswith("<<Lead Assigned>>")
        )



        if is_new_ticket:
            values["subject"] = (
                f"<<New Ticket>> {self._adi_email_subject()}"
            )
        elif is_lead_assignment:
            values["subject"] = message.subject
        elif is_rating_request:
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

    def message_post(self, **kwargs):
        """
        Standardise Helpdesk Ticket Created messages and
        customer reply email presentation.

        - Ticket Created chatter remains minimal.
        - Raw email content is preserved in ticket.description.
        - Customer Discussions use the ADI customer reply layout.
        - Internal Notes and other Helpdesk messages are untouched.
        """

        ticket_created_subtype = self.env.ref(
            "helpdesk.mt_ticket_new",
            raise_if_not_found=False,
        )

        subtype_id = kwargs.get("subtype_id")

        is_ticket_created_message = (
            len(self) == 1
            and ticket_created_subtype
            and subtype_id == ticket_created_subtype.id
        )

        # ---------------------------------------------------------
        # Ticket Created
        # ---------------------------------------------------------

        if is_ticket_created_message:
            ticket = self[0]
            team = ticket.team_id
            author = team.adi_message_author_id

            kwargs = dict(kwargs)

            original_body = kwargs.get("body")
            message_type = kwargs.get("message_type")

            # -------------------------------------------------
            # Raw email ticket creation
            # -------------------------------------------------
            #
            # Preserve the incoming email body as the Problem
            # before removing the duplicate chatter content.
            #
            # Website tickets already have description populated.
            # -------------------------------------------------

            if (
                message_type == "email"
                and original_body
                and not ticket.description
            ):
                ticket.write({
                    "description": original_body,
                })

            # Keep Ticket Created chatter minimal.
            kwargs["body"] = ""

            kwargs["email_layout_xmlid"] = (
                "adi_helpdesk_custom."
                "adi_helpdesk_new_ticket_notification"
            )

            if author:
                kwargs.update({
                    "author_id": author.id,
                    "email_from": (
                        f"{team.name} <{team.alias_email}>"
                        if team.alias_email
                        else author.email_formatted
                    ),
                })

        # ---------------------------------------------------------
        # Customer reply email layout
        # ---------------------------------------------------------
        #
        # This block MUST be outside the Ticket Created block.
        #
        # Customer-originated Discussions remain authored by the
        # customer but are redistributed using the standard ADI
        # Helpdesk presentation.
        # ---------------------------------------------------------

        if not is_ticket_created_message:
            author_id = kwargs.get("author_id")
            message_type = kwargs.get("message_type")
            subtype_id = kwargs.get("subtype_id")

            discussion_subtype = self.env.ref(
                "mail.mt_comment",
                raise_if_not_found=False,
            )

            author = (
                self.env["res.partner"].browse(author_id).exists()
                if author_id
                else self.env["res.partner"]
            )

            internal_user = (
                author.user_ids.filtered(
                    lambda user:
                        user.active
                        and not user.share
                )
                if author
                else self.env["res.users"]
            )

            is_customer_reply = (
                len(self) == 1
                and author
                and not internal_user
                and message_type in ("email", "comment")
                and discussion_subtype
                and subtype_id == discussion_subtype.id
            )

            if is_customer_reply:
                kwargs = dict(kwargs)

                kwargs["email_layout_xmlid"] = (
                    "adi_helpdesk_custom."
                    "adi_helpdesk_customer_reply_notification"
                )

        return super().message_post(**kwargs)

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

            kwargs = dict(kwargs)

            # Customer acknowledgement has an explicit customer recipient.
            # Give it a dedicated hidden subtype so normal ticket followers
            # are not also notified.
            kwargs["subtype_id"] = self.env.ref(
                "adi_helpdesk_custom.mt_customer_acknowledgement"
            ).id

            if author:
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

    adi_show_management_card = fields.Boolean(
        compute="_compute_adi_show_management_card",
    )

    @api.depends("stage_id")
    def _compute_adi_show_management_card(self):
        for ticket in self:
            ticket.adi_show_management_card = (
                ticket.stage_id.name != "New"
            )
            

    #-------------------------------------------------------------
    # Notification Contact Name / Company Name  
    #-------------------------------------------------------------

    @api.depends(
        "partner_id",
        "partner_id.parent_id",
        "partner_id.parent_id.adi_helpdesk_partner",
        "adi_matched_company_id",
        "adi_matched_company_id.name",
        "adi_submitted_email",
        "adi_submitted_company_name",
        "adi_submitted_contact_name",
    )
    def _compute_adi_notification_contact(self):
        Partner = self.env["res.partner"]

        for ticket in self:
            company_name = (
                ticket.adi_submitted_company_name
                or False
            )

            contact_name = (
                ticket.adi_submitted_contact_name
                or False
            )

            # -----------------------------------------------------
            # Recognised contact
            # -----------------------------------------------------

            if ticket.partner_id:
                contact = ticket.partner_id

                contact_name = (
                    contact.name
                    or contact_name
                )

                # The explicitly resolved customer company always
                # takes priority.
                if ticket.adi_matched_company_id:
                    company_name = (
                        ticket.adi_matched_company_id.name
                        or company_name
                    )

                else:
                    parent_company = (
                        contact.parent_id
                        or contact.commercial_partner_id
                    )

                    # A Helpdesk Partner contact may represent more
                    # than one customer company. Until Set In Progress
                    # resolves the customer, do not present the Partner
                    # itself as though it were the customer.
                    if (
                        parent_company
                        and parent_company.adi_helpdesk_partner
                    ):
                        company_name = "Partner - Company TBD"

                    elif parent_company:
                        company_name = (
                            parent_company.name
                            or company_name
                        )

            # -----------------------------------------------------
            # Submitted email without partner_id
            # -----------------------------------------------------

            elif ticket.adi_submitted_email:
                contact = Partner.search([
                    (
                        "email",
                        "=ilike",
                        ticket.adi_submitted_email,
                    ),
                    ("active", "=", True),
                ], limit=1)

                if contact:
                    contact_name = (
                        contact.name
                        or contact_name
                    )

                    if ticket.adi_matched_company_id:
                        company_name = (
                            ticket.adi_matched_company_id.name
                            or company_name
                        )

                    else:
                        parent_company = (
                            contact.parent_id
                            or contact.commercial_partner_id
                        )

                        if (
                            parent_company
                            and parent_company.adi_helpdesk_partner
                        ):
                            company_name = "Partner - Company TBD"

                        elif parent_company:
                            company_name = (
                                parent_company.name
                                or company_name
                            )

            ticket.adi_notification_company_name = (
                company_name
                or "-"
            )

            ticket.adi_notification_contact_name = (
                contact_name
                or "-"
            )

    #-------------------------------------------------------------
    # Follower Subtype Configuration
    #-------------------------------------------------------------

    def _adi_configure_follower_subtypes(self, partner_ids=None):
        """
        Enforce ADI Helpdesk follower notification preferences.

        - All Helpdesk followers receive Discussions.
        - Internal @adi.com followers also receive Notes.
        """

        discussion_subtype = self.env.ref(
            "mail.mt_comment",
            raise_if_not_found=False,
        )
        note_subtype = self.env.ref(
            "mail.mt_note",
            raise_if_not_found=False,
        )

        if not discussion_subtype or not note_subtype:
            return

        for ticket in self:
            followers = ticket.message_follower_ids

            if partner_ids:
                followers = followers.filtered(
                    lambda follower:
                        follower.partner_id.id in partner_ids
                )

            for follower in followers:
                partner = follower.partner_id

                if not partner:
                    continue

                subtype_commands = []

                if discussion_subtype not in follower.subtype_ids:
                    subtype_commands.append(
                        (4, discussion_subtype.id)
                    )

                if (
                    partner.email
                    and partner.email.lower().endswith("@adi.com")
                    and note_subtype not in follower.subtype_ids
                ):
                    subtype_commands.append(
                        (4, note_subtype.id)
                    )

                if subtype_commands:
                    follower.write({
                        "subtype_ids": subtype_commands,
                    })

    def message_subscribe(
        self,
        partner_ids=None,
        subtype_ids=None,
    ):
        result = super().message_subscribe(
            partner_ids=partner_ids,
            subtype_ids=subtype_ids,
        )

        self._adi_configure_follower_subtypes(
            partner_ids=partner_ids,
        )

        return result

    def message_update(self, msg, update_vals=None):
        """
        Process inbound Helpdesk replies.

        - Replies from internal Odoo users are treated as internal notes.
        - Customer replies remain normal discussions.
        - Quoted email history is removed before the message is posted
        into Helpdesk chatter.
        """


        # ---------------------------------------------------------
        # Internal / customer routing
        # ---------------------------------------------------------

        author = self.env["res.partner"].browse(
            msg.get("author_id")
        ).exists()

        internal_user = (
            author.user_ids.filtered(
                lambda user:
                    user.active
                    and not user.share
            )
            if author
            else self.env["res.users"]
        )

        # ---------------------------------------------------------
        # Normalise incoming sender display name
        # ---------------------------------------------------------
        #
        # Keep the actual sender email address, but use the
        # recognised Helpdesk contact's name as the display name.
        # ---------------------------------------------------------

        if author and msg.get("email_from"):
            _sender_name, sender_email = parseaddr(
                msg["email_from"]
            )

            if sender_email:
                msg["email_from"] = formataddr(
                    (author.name, sender_email)
                )


        msg["is_internal"] = False


        # ---------------------------------------------------------
        # Remove quoted email history
        # ---------------------------------------------------------

        body = msg.get("body") or ""

        if body:
            try:
                root = lxml.html.fragment_fromstring(
                    str(body),
                    create_parent="div",
                )

                changed = False

                # -------------------------------------------------
                # First choice:
                # Find the current Outlook From / Sent / To / Subject
                # boundary.
                #
                # This works for both the ADI internal reply and the
                # customer-facing reply, even if older nested emails
                # already contain Odoo quote markers.
                # -------------------------------------------------

                quote_start = None

                for paragraph in root.xpath(".//p"):
                    text = " ".join(paragraph.itertext())
                    text = " ".join(text.split()).lower()

                    if (
                        "from:" in text
                        and "sent:" in text
                        and "to:" in text
                        and "subject:" in text
                    ):
                        quote_start = paragraph

                        parent = quote_start.getparent()

                        if (
                            parent is not None
                            and parent.tag == "div"
                        ):
                            quote_start = parent
                            parent = quote_start.getparent()

                            if (
                                parent is not None
                                and parent.tag == "div"
                            ):
                                quote_start = parent

                        break

                if quote_start is not None:
                    parent = quote_start.getparent()

                    if parent is not None:
                        children = list(parent)
                        start_index = children.index(quote_start)

                        for child in children[start_index:]:
                            parent.remove(child)

                        changed = True


                # -------------------------------------------------
                # Fallback:
                # If there is no Outlook header, remove content
                # that Odoo itself has already identified as quoted.
                # -------------------------------------------------

                if not changed:
                    quoted_nodes = root.xpath(
                        './/*[@data-o-mail-quote="1" '
                        'and not(ancestor::*[@data-o-mail-quote="1"])]'
                    )

                    for node in quoted_nodes:
                        parent = node.getparent()

                        if parent is not None:
                            parent.remove(node)
                            changed = True


                # -------------------------------------------------
                # Save cleaned body
                # -------------------------------------------------

                if changed:
                    cleaned_body = "".join(
                        etree.tostring(
                            child,
                            encoding="unicode",
                            method="html",
                        )
                        for child in root
                    )

                    if cleaned_body.strip():
                        msg["body"] = Markup(
                            cleaned_body
                        )

            except (ValueError, etree.ParserError):
                # Unusual email HTML: leave it untouched rather
                # than risk losing genuine message content.
                pass


        return super().message_update(
            msg,
            update_vals=update_vals,
        )


    #-------------------------------------------------------------
    # Inbound Raw Email Processing
    #-------------------------------------------------------------

    @api.model
    def message_new(self, msg, custom_values=None):
        """
        Process new inbound Helpdesk emails without allowing
        Odoo to auto-create Contacts for unknown senders.
        """

        return super(
            HelpdeskTicket,
            self.with_context(
                adi_helpdesk_no_partner_autocreate=True,
            ),
        ).message_new(
            msg,
            custom_values=custom_values,
        )




