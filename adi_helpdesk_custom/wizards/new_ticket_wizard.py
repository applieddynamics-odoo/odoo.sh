from odoo import api, fields, models
from odoo.exceptions import UserError


class AdiHelpdeskNewTicketWizard(models.TransientModel):
    _name = "adi.helpdesk.new.ticket.wizard"
    _description = "Create Internal Helpdesk Ticket"

    selectable_company_ids = fields.Many2many(
        "res.partner",
        string="Selectable Companies",
        compute="_compute_selectable_company_ids",
    )

    company_id = fields.Many2one(
        "res.partner",
        string="Company",
        required=True,
    )

    allowed_contact_ids = fields.Many2many(
        "res.partner",
        string="Allowed Contacts",
        compute="_compute_allowed_contact_ids",
    )

    contact_id = fields.Many2one(
        "res.partner",
        string="Contact",
        required=True,
        context={"adi_show_contact_name_only": True},
    )

    email = fields.Char(
        string="Email",
        readonly=True,
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

    # ---------------------------------------------------------
    # Companies available in the manual New Ticket wizard
    # ---------------------------------------------------------

    def _compute_selectable_company_ids(self):
        Partner = self.env["res.partner"]

        approved_companies = Partner.search([
            ("is_company", "=", True),
            ("active", "=", True),
            ("adi_helpdesk_approved_company", "=", True),
        ])

        # Approved companies that already have at least one usable
        # direct contact.
        direct_contacts = Partner.search([
            ("is_company", "=", False),
            ("active", "=", True),
            ("email", "!=", False),
            ("parent_id", "in", approved_companies.ids),
        ])

        selectable_company_ids = set(
            direct_contacts.mapped("parent_id").ids
        )

        # Helpdesk Partners that have at least one usable contact.
        helpdesk_partners = Partner.search([
            ("is_company", "=", True),
            ("active", "=", True),
            ("adi_helpdesk_partner", "=", True),
            ("child_ids.is_company", "=", False),
            ("child_ids.active", "=", True),
            ("child_ids.email", "!=", False),
        ])

        # Any approved customer company supported by one of those
        # Partners is also useful in the manual wizard, even when
        # the customer company has no direct emailed contact.
        for partner in helpdesk_partners:
            supported_companies = (
                partner.adi_helpdesk_customer_company_ids.filtered(
                    lambda company:
                        company.active
                        and company.is_company
                        and company.adi_helpdesk_approved_company
                )
            )

            selectable_company_ids.update(
                supported_companies.ids
            )

            # If the Partner itself is also an approved customer,
            # its own contacts may raise tickets for its equipment.
            if partner.adi_helpdesk_approved_company:
                selectable_company_ids.add(partner.id)

        for wizard in self:
            wizard.selectable_company_ids = Partner.browse(
                list(selectable_company_ids)
            )

    # ---------------------------------------------------------
    # Contacts authorised for the selected customer company
    # ---------------------------------------------------------

    @api.depends("company_id")
    def _compute_allowed_contact_ids(self):
        Partner = self.env["res.partner"]

        for wizard in self:
            if not wizard.company_id:
                wizard.allowed_contact_ids = Partner
                continue

            # Direct contacts belonging to the selected customer.
            direct_contacts = Partner.search([
                ("parent_id", "=", wizard.company_id.id),
                ("is_company", "=", False),
                ("active", "=", True),
                ("email", "!=", False),
            ])

            # Partner companies explicitly authorised to support
            # this customer company.
            helpdesk_partners = Partner.search([
                ("is_company", "=", True),
                ("active", "=", True),
                ("adi_helpdesk_partner", "=", True),
                (
                    "adi_helpdesk_customer_company_ids",
                    "in",
                    [wizard.company_id.id],
                ),
            ])

            partner_contacts = Partner.search([
                ("parent_id", "in", helpdesk_partners.ids),
                ("is_company", "=", False),
                ("active", "=", True),
                ("email", "!=", False),
            ])

            wizard.allowed_contact_ids = (
                direct_contacts | partner_contacts
            )

    @api.onchange("company_id")
    def _onchange_company_id(self):
        self.contact_id = False
        self.email = False

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

        if self.contact_id not in self.allowed_contact_ids:
            raise UserError(
                "The selected contact is not authorised to support "
                "the selected customer company."
            )

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
                self.adi_customer_reference_number or "None"
            ),
            "adi_new_contact_review_required": False,

            # The Company selected at the start of the manual
            # process is always the actual customer company.
            "adi_matched_company_id": self.company_id.id,
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