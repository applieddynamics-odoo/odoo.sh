from odoo import fields, models


class AdiHelpdeskIssueType(models.Model):
    _name = "adi.helpdesk.issue.type"
    _description = "ADI Helpdesk Issue Type"
    _order = "sequence, name"

    name = fields.Char(
        string="Issue Type",
        required=True,
    )

    sequence = fields.Integer(
        default=10,
    )

    active = fields.Boolean(
        default=True,
    )