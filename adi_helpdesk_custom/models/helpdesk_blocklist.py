from odoo import api, fields, models


class AdiHelpdeskBlocklist(models.Model):
    _name = "adi.helpdesk.blocklist"
    _description = "Helpdesk Blocked Sender"
    _order = "value"

    block_type = fields.Selection(
        [
            ("email", "Email"),
        ],
        string="Block Type",
        required=True,
        default="email",
    )

    value = fields.Char(
        string="Email Address",
        required=True,
        help="Email address to block, for example spam@example.com.",
    )

    reason = fields.Text(
        string="Reason",
    )


    _sql_constraints = [
        (
            "unique_block_type_value",
            "unique(block_type, value)",
            "This email address is already blocked.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["block_type"] = "email"
            if vals.get("value"):
                vals["value"] = vals["value"].strip().lower()
        return super().create(vals_list)

    def write(self, vals):
        vals.pop("block_type", None)
        if vals.get("value"):
            vals["value"] = vals["value"].strip().lower()
        return super().write(vals)