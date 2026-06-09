from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    adi_approved_helpdesk_domain = fields.Char(
        string="Approved Helpdesk Email Domain",
        help="Example: customer.com. Website Helpdesk tickets from this domain can bypass the Validity Check stage.",
    )

    @api.depends_context("adi_show_contact_name_only")
    def _compute_display_name(self):
        if not self.env.context.get("adi_show_contact_name_only"):
            return super()._compute_display_name()

        for partner in self:
            partner.display_name = partner.name or ""