from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MailActivity(models.Model):
    _inherit = "mail.activity"

    is_controlled_workflow_activity = fields.Boolean(
        string="Controlled Workflow Activity",
        default=False,
        copy=False,
        index=True,
    )

    def _check_controlled_workflow_activity(self):
        if self.env.context.get("bypass_locked_workflow_activity"):
            return

        if self.env.user.has_group("adi_improvement_app.group_workflow_activity_override"):
            return

        for rec in self:
            if rec.is_controlled_workflow_activity:
                raise ValidationError(_(
                    "This activity is managed by the workflow and is read-only here. "
                    "Please use the form buttons on the parent record."
                ))

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def write(self, vals):
        protected_fields = {
            "activity_type_id",
            "summary",
            "note",
            "date_deadline",
            "user_id",
            "res_id",
            "res_model_id",
        }
        if protected_fields.intersection(vals.keys()):
            self._check_controlled_workflow_activity()
        return super().write(vals)

    def unlink(self):
        self._check_controlled_workflow_activity()
        return super().unlink()

    def action_feedback(self, feedback=False, attachment_ids=None):
        self._check_controlled_workflow_activity()
        return super().action_feedback(
            feedback=feedback,
            attachment_ids=attachment_ids,
        )
    