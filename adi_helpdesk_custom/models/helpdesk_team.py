from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    adi_message_author_id = fields.Many2one(
        comodel_name="res.partner",
        string="Automated Message Author",
        help=(
            "Contact shown as the author of automated messages sent "
            "on behalf of this Helpdesk team."
        ),
    )