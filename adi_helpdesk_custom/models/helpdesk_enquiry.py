from odoo import fields, models


class AdiHelpdeskEnquiry(models.Model):
    _name = "adi.helpdesk.enquiry"
    _description = "Helpdesk Customer Enquiry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(string="Subject", required=True, tracking=True)
    contact_name = fields.Char(string="Contact Name", required=True)
    company_name = fields.Char(string="Company Name", required=True)
    email = fields.Char(string="Email", required=True)
    phone = fields.Char(string="Phone")
    message = fields.Text(string="Message", required=True)

    state = fields.Selection(
        [
            ("new", "New"),
            ("reviewing", "Reviewing"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="new",
        tracking=True,
    )