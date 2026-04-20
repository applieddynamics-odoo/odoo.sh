# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RolesResponsibility(models.Model):
    _name = "adi_improvement_app.roles_responsibility"
    _description = "Roles and Responsibilities"
    _rec_name = "name"

    name = fields.Char(required=True, default="Default")
    active = fields.Boolean(default=True)

    quality_lead_line_ids = fields.One2many(
        "adi_improvement_app.roles_responsibility.line",
        "config_id",
        string="Quality Lead Assignment Order",
    )

    @api.constrains("active")
    def _check_single_active_record(self):
        for rec in self:
            if rec.active:
                other = self.search(
                    [
                        ("id", "!=", rec.id),
                        ("active", "=", True),
                    ],
                    limit=1,
                )
                if other:
                    raise ValidationError(
                        _("Only one active Roles and Responsibilities record is allowed.")
                    )


class RolesResponsibilityLine(models.Model):
    _name = "adi_improvement_app.roles_responsibility.line"
    _description = "Roles and Responsibilities Line"
    _order = "sequence, id"

    config_id = fields.Many2one(
        "adi_improvement_app.roles_responsibility",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    user_id = fields.Many2one(
        "res.users",
        required=True,
        string="User",
    )