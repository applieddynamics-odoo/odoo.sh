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
            ("adi_approved_helpdesk_domain", "!=", False),
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

    @api.onchange("company_id")
    def _onchange_company_id(self):
        self.contact_id = False
        self.email = False

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

        new_stage = self.env["helpdesk.stage"].search(
            [("name", "=", "New")],
            limit=1,
        )

        if not new_stage:
            raise UserError("Could not find a Helpdesk stage called 'New'.")

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
            "adi_software_version_id": self.adi_software_version_id.id,
            "adi_customer_input_serial_number": self.adi_customer_input_serial_number,
            "adi_customer_reference_number": self.adi_customer_reference_number or "None",
            "adi_validity_check_required": False,
            "adi_new_contact_review_required": False,
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