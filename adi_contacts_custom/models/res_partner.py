from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    adi_helpdesk_approved_company = fields.Boolean(
        string="Helpdesk Approved Company",
        default=False,
        help="Tick this box when this company is approved to use the ADI Helpdesk.",
    )

    @api.depends_context("adi_show_contact_name_only")
    def _compute_display_name(self):
        if not self.env.context.get("adi_show_contact_name_only"):
            return super()._compute_display_name()

        for partner in self:
            partner.display_name = partner.name or ""