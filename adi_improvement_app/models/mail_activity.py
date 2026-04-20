from odoo import api, fields, models, _
from datetime import timedelta

class MailActivity(models.Model):
    _inherit = "mail.activity"

    @api.model_create_multi
    def create(self, vals_list):
        activities = super().create(vals_list)

        if self.env.context.get("adi_verification_flow"):
            for activity in activities:
                if (
                    activity.res_model == "adi_improvement_app.improvement"
                    and activity.res_id
                ):
                    improvement = self.env["adi_improvement_app.improvement"].browse(activity.res_id)
                    if improvement.exists() and improvement.status == "in_progress":
                        improvement.status = "awaiting_verification"
                        improvement.date_submitted_for_verification = fields.Date.context_today(improvement)
                        improvement.message_post(
                            body=_(
                                "CI submitted for Effectiveness Review by %s on %s. "
                                "Review activity assigned to %s with due date %s."
                            ) % (
                                self.env.user.name,
                                fields.Date.context_today(improvement).strftime("%d %b %Y"),
                                activity.user_id.name,
                                activity.date_deadline.strftime("%d %b %Y") if activity.date_deadline else "",
                            )
                        )

        return activities
    
    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)

        if self.env.context.get("adi_verification_flow"):
            res_model = self.env.context.get("default_res_model")
            res_id = self.env.context.get("default_res_id")

            if res_model == "adi_improvement_app.improvement" and res_id:
                improvement = self.env[res_model].browse(res_id)
                if improvement.exists():
                    assignee = improvement._get_verification_assignee()
                    vals["user_id"] = assignee.id
                    vals["date_deadline"] = fields.Date.context_today(improvement) + timedelta(days=14)

        return vals


