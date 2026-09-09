from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    adi_helpdesk_approved_company = fields.Boolean(
        string="Helpdesk Approved Company",
        default=False,
        help=(
            "Tick this box when this company is approved "
            "to use the ADI Helpdesk."
        ),
    )

    adi_helpdesk_partner = fields.Boolean(
        string="Helpdesk Partner",
        default=False,
        help=(
            "Tick this box when this company is authorised by ADI "
            "to raise and manage Helpdesk tickets on behalf of "
            "other approved customer companies."
        ),
    )

    adi_helpdesk_customer_company_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="adi_helpdesk_partner_customer_rel",
        column1="partner_company_id",
        column2="customer_company_id",
        string="Helpdesk Customer Companies",
        domain=[
            ("is_company", "=", True),
            ("active", "=", True),
            ("adi_helpdesk_approved_company", "=", True),
        ],
        help=(
            "Approved customer companies that this Helpdesk Partner "
            "is authorised to support."
        ),
    )

    @api.depends_context("adi_show_contact_name_only")
    def _compute_display_name(self):
        if not self.env.context.get("adi_show_contact_name_only"):
            return super()._compute_display_name()

        for partner in self:
            partner.display_name = partner.name or ""