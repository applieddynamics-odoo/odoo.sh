from odoo import api, fields, models
from odoo.exceptions import UserError


class AdiHelpdeskNewTicketWizard(models.TransientModel):
    _name = "adi.helpdesk.new.ticket.wizard"
    _description = "Create Internal Helpdesk Ticket"

    company_id = fields.Many2one(
        "res.partner",
        string="Company",
        required=True,
        domain=[
            ("is_company", "=", True),
            ("active", "=", True),
            ("adi_helpdesk_approved_company", "=", True),
            ("child_ids.is_company", "=", False),
            ("child_ids.active", "=", True),
            ("child_ids.email", "!=", False),
        ],
    )

    contact_id = fields.Many2one(
        "res.partner",
        string="Contact",
        required=True,
        domain="[('parent_id', '=', company_id), ('is_company', '=', False), ('active', '=', True), ('email', '!=', False)]",
        context={"adi_show_contact_name_only": True},
    )

    email = fields.Char(
        string="Email",
        readonly=True,
    )

    is_helpdesk_partner = fields.Boolean(
        related="company_id.adi_helpdesk_partner",
        string="Helpdesk Partner",
        readonly=True,
    )

    allowed_customer_company_ids = fields.Many2many(
        "res.partner",
        string="Allowed Customer Companies",
        compute="_compute_allowed_customer_company_ids",
    )

    customer_company_id = fields.Many2one(
        "res.partner",
        string="Customer Company",
    )

    ticket_type_id = fields.Many2one(
        "helpdesk.ticket.type",
        string="Issue Type",
        required=True,
    )

    adi_software_version_id = fields.Many2one(
        "adi.helpdesk.software.version",
        string="Software Version",
    )

    adi_customer_input_serial_number = fields.Char(
        string="Asset / Serial No",
        required=False,
    )

    adi_customer_reference_number = fields.Char(
        string="Customer Reference Number",
        default="None",
        required=False,
    )

    name = fields.Char(
        string="Subject",
        required=True,
    )

    description = fields.Html(
        string="Problem",
        required=True,
    )

    @api.depends(
        "company_id",
        "company_id.adi_helpdesk_partner",
        "company_id.adi_helpdesk_approved_company",
        "company_id.adi_helpdesk_customer_company_ids",
        "company_id.adi_helpdesk_customer_company_ids.active",
        "company_id.adi_helpdesk_customer_company_ids.adi_helpdesk_approved_company",
    )
    def _compute_allowed_customer_company_ids(self):
        for wizard in self:
            allowed_companies = self.env["res.partner"]

            if (
                wizard.company_id
                and wizard.company_id.adi_helpdesk_partner
            ):
                # The Partner itself may be the actual customer
                # where it owns equipment being supported.
                if (
                    wizard.company_id.active
                    and wizard.company_id.is_company
                    and wizard.company_id.adi_helpdesk_approved_company
                ):
                    allowed_companies |= wizard.company_id

                # Add the approved customer companies that this
                # Partner is authorised to support.
                allowed_companies |= (
                    wizard.company_id
                    .adi_helpdesk_customer_company_ids
                    .filtered(
                        lambda company:
                            company.active
                            and company.is_company
                            and company.adi_helpdesk_approved_company
                    )
                )

            wizard.allowed_customer_company_ids = allowed_companies

    @api.onchange("company_id")
    def _onchange_company_id(self):
        self.contact_id = False
        self.email = False
        self.customer_company_id = False

        return {
            "domain": {
                "contact_id": [
                    ("parent_id", "=", self.company_id.id),
                    ("is_company", "=", False),
                    ("active", "=", True),
                    ("email", "!=", False),
                ]
            }
        }

    @api.onchange("contact_id")
    def _onchange_contact_id(self):
        self.email = self.contact_id.email or False

    def action_create_ticket(self):
        self.ensure_one()

        if not self.contact_id.email:
            raise UserError(
                "The selected contact does not have an email address. "
                "Please update the contact record before creating the ticket."
            )

        # ---------------------------------------------------------
        # Determine the actual customer company.
        #
        # Normal company:
        #   The selected Company is the customer.
        #
        # Helpdesk Partner:
        #   The user must explicitly select which authorised
        #   customer company the ticket relates to.
        # ---------------------------------------------------------

        if self.is_helpdesk_partner:
            if not self.customer_company_id:
                raise UserError(
                    "Please select the Customer Company that this "
                    "Partner is raising the ticket for."
                )

            if (
                self.customer_company_id
                not in self.allowed_customer_company_ids
            ):
                raise UserError(
                    "The selected Customer Company is not authorised "
                    "for this Helpdesk Partner."
                )

            actual_customer_company = self.customer_company_id

        else:
            actual_customer_company = self.company_id

        new_stage = self.env["helpdesk.stage"].search(
            [("name", "=", "New")],
            limit=1,
        )

        if not new_stage:
            raise UserError(
                "Could not find a Helpdesk stage called 'New'."
            )

        ticket = self.env["helpdesk.ticket"].with_context(
            adi_internal_ticket_create=True,
        ).create({
            "name": self.name,
            "description": self.description,
            "stage_id": new_stage.id,
            "partner_id": self.contact_id.id,
            "partner_email": self.contact_id.email,
            "partner_name": self.contact_id.name,
            "ticket_type_id": self.ticket_type_id.id,
            "adi_software_version_id": (
                self.adi_software_version_id.id
            ),
            "adi_customer_input_serial_number": (
                self.adi_customer_input_serial_number
            ),
            "adi_customer_reference_number": (
                self.adi_customer_reference_number
                or "None"
            ),
            "adi_new_contact_review_required": False,
            "adi_matched_company_id": (
                actual_customer_company.id
            ),
        })

        return {
            "type": "ir.actions.act_window",
            "name": "Set to In Process",
            "res_model": "adi.helpdesk.set.in.progress.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_ticket_id": ticket.id,
                "default_user_id": False,
                "adi_open_ticket_after_set_in_progress": True,
            },
        }