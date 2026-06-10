from odoo import fields, models


class AdiHelpdeskSoftwareVersion(models.Model):
    _name = "adi.helpdesk.software.version"
    _description = "ADI Helpdesk Software Version"
    _order = "sequence, name"

    name = fields.Char(
        string="Software Version",
        required=True,
    )

    sequence = fields.Integer(
        default=10,
    )

    active = fields.Boolean(
        default=True,
    )