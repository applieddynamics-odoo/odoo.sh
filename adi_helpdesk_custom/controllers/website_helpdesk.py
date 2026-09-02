from odoo import http
from odoo.http import request


class AdiWebsiteHelpdesk(http.Controller):

    @http.route(
        "/adi/helpdesk/check_email",
        type="json",
        auth="public",
        website=True,
        csrf=False,
    )
    def adi_check_helpdesk_email(self, email=None):
        email = (email or "").strip().lower()

        if not email or "@" not in email:
            return {"recognised": False}

        contact = request.env["res.partner"].sudo().search([
            ("email", "=ilike", email),
            ("active", "=", True),
            ("is_company", "=", False),
            ("parent_id", "!=", False),
        ], limit=1)

        return {
            "recognised": bool(contact),
        }