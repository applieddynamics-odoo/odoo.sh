from odoo import api, fields, models


class AdiHelpdeskBlocklist(models.Model):
    _name = "adi.helpdesk.blocklist"
    _description = "Helpdesk Blocked Sender or Domain"
    _order = "block_type, value"

    block_type = fields.Selection(
        [
            ("email", "Email"),
            ("domain", "Domain"),
        ],
        string="Block Type",
        required=True,
        default="email",
    )

    value = fields.Char(
        string="Value",
        required=True,
        help="Use an email address such as spam@example.com or a domain such as example.com.",
    )

    reason = fields.Text(
        string="Reason",
    )

    active = fields.Boolean(
        default=True,
    )

    _sql_constraints = [
        (
            "unique_block_type_value",
            "unique(block_type, value)",
            "This email or domain is already blocked.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("value"):
                vals["value"] = vals["value"].strip().lower()
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("value"):
            vals["value"] = vals["value"].strip().lower()
        return super().write(vals)