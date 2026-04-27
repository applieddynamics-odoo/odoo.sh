from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

SOURCE = [
    ("Internal Audit Finding", "Internal Audit Finding"),
    ("External Audit Finding", "External Audit Finding"),
    ("Customer Request", "Customer Request"),
    ("Internal Opportunity Identified", "Internal Opportunity Identified"),
    ("Lessons Learnt", "Lessons Learnt"),
    ("Corrective Action Report (CAR)", "Corrective Action Report (CAR)"),
]

TYPE = [
    ("local", "Local Improvement"),
    ("process", "Process Improvement"),
    ("strategic", "Strategic Improvement"),
]  

STATUS = [
    ("open", "Open"),
    ("in_progress", "In Progress"),
    ("on_hold", "On Hold"),
    ("awaiting_verification", "Awaiting Closure "),
    ("closed", "Closed"),
]

CI_VERIFICATION_RESULT = [
    ("achieved", "Closure Approved"),
    ("further_action", "Further Action Required"),
    ("abort", "Not implemented"),
]    

class CiImprovement(models.Model):
    _name = "adi_improvement_app.improvement"
    _description = "Continuous Improvement"
    _rec_name = "action_reference"
    _inherit = ["adi_improvement_app.imp_common", "mail.thread", "mail.activity.mixin"]

    status = fields.Selection(STATUS, default="open")
    source = fields.Selection(SOURCE)
    type = fields.Selection(TYPE, default="")
    owner = fields.Char(string="Owner (legacy)")
    summary = fields.Text()
    notes = fields.Text()
    actions = fields.Text()
    progress_updates = fields.Text(string="Progress Updates / Notes")
    date_due = fields.Date()

    date_in_progress = fields.Date(string="Date In Progress", readonly=False)
    date_submitted_for_verification = fields.Date(
        string="Submitted for Closure", 
        readonly=False,
    )

    ci_date_done = fields.Date(string="CI Done Date", readonly=False)
    verified_by = fields.Many2one("res.users", string="Reviewed By", readonly=False)
    verification_result = fields.Selection(CI_VERIFICATION_RESULT, readonly=True)
    closure_statement = fields.Text()

    def _create_controlled_activity(self, activity_type, user, due_date, summary, note=False):
        self.ensure_one()

        controlled_summary = _("[WORKFLOW] %s") % summary

        guidance = ""
        if note:
            guidance = _(
                "<div style='margin-top:4px;'>"
                "💬 <strong>Guidance / notes:</strong><br/>%s"
                "</div>"
            ) % note

        warning = _(
            "<div style='margin-top:12px; color:#6c757d; font-size:13px;'>"
            "🔒 <strong>Workflow controlled activity:</strong> "
            "Use the form buttons to manage this activity."
            "</div>"
        )

        full_note = guidance
        if full_note:
            full_note = "%s<br/>%s" % (full_note, warning)
        else:
            full_note = warning

        return self.env["mail.activity"].create({
            "activity_type_id": activity_type.id,
            "summary": controlled_summary,
            "note": full_note,
            "date_deadline": due_date,
            "user_id": user.id,
            "res_id": self.id,
            "res_model_id": self.env["ir.model"]._get_id(self._name),
            "is_controlled_workflow_activity": True,
        })

    def _get_owner_user(self):
        self.ensure_one()
        if not self.owner_id:
            raise ValidationError(_("Please set an Owner before continuing."))
        return self.owner_id

    def _get_roles_config(self):
        config = self.env["adi_improvement_app.roles_responsibility"].search(
            [("active", "=", True)],
            limit=1,
        )
        if not config:
            raise ValidationError(_("No active Roles and Responsibilities configured."))
        return config

    def _get_verification_assignee(self):
        self.ensure_one()

        config = self._get_roles_config()
        owner_user = self._get_owner_user()

        lines = config.quality_lead_line_ids.sorted(key=lambda l: (l.sequence, l.id))
        if not lines:
            raise ValidationError(_("No Quality Lead users configured."))

        for line in lines:
            if line.user_id != owner_user:
                return line.user_id

        raise ValidationError(_("No alternative Quality Lead available."))

    def _get_review_activity_type(self):
        return self.env.ref("adi_improvement_app.mail_activity_type_review")

    def _get_rework_activity_type(self):
        return self.env.ref("adi_improvement_app.mail_activity_type_rework")

    def _get_open_verification_activity(self):
        self.ensure_one()
        activity_type = self._get_review_activity_type()
        return self.activity_ids.filtered(
            lambda a: a.activity_type_id == activity_type
        )[:1]

    def _get_open_rework_activity(self):
        self.ensure_one()
        activity_type = self._get_rework_activity_type()
        return self.activity_ids.filtered(
            lambda a: a.activity_type_id == activity_type
        )[:1]

    def _close_open_rework_activity(self):
        self.ensure_one()
        activity = self._get_open_rework_activity()
        if activity:
            activity.with_context(bypass_locked_workflow_activity=True).write({"note": False})
            activity.with_context(bypass_locked_workflow_activity=True).action_feedback(feedback="")
        return activity

    def _create_rework_activity(self, note):
        self.ensure_one()

        owner_user = self._get_owner_user()
        activity_type = self._get_rework_activity_type()
        due_date = fields.Date.context_today(self) + timedelta(days=7)
        reference = self.action_reference or self.display_name

        return self._create_controlled_activity(
            activity_type=activity_type,
            user=owner_user,
            due_date=due_date,
            summary=_("%s Rework Improvement") % reference,
            note=note,
        )

    def action_set_in_progress(self):
        for rec in self:
            if not rec.date_due:
                raise ValidationError(_("Please set a Due Date first."))

            rec.status = "in_progress"
            if not rec.date_in_progress:
                rec.date_in_progress = fields.Date.context_today(rec)

            rec.message_post(
                body=_("CI moved to In Progress by %s on %s.")
                % (
                    self.env.user.name,
                    fields.Date.context_today(rec).strftime("%d %b %Y"),
                )
            )

    def action_set_on_hold(self):
        for rec in self:
            rec.status = "on_hold"
            rec.message_post(
                body=_("CI placed On Hold by %s on %s.")
                % (
                    self.env.user.name,
                    fields.Date.context_today(rec).strftime("%d %b %Y"),
                )
            )

    def action_open_closure_wizard(self):
        self.ensure_one()

        if self.status not in ("open", "in_progress", "on_hold"):
            raise ValidationError(
                _("This record can only be cancelled from Open, In Progress, or On Hold.")
            )

        return {
            "type": "ir.actions.act_window",
            "name": f"{self.action_reference} - Closure Status",
            "res_model": "adi_improvement_app.ci_verification_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_ci_id": self.id,
                "default_verification_result": "abort",
                "default_closure_statement": self.closure_statement,
                "closure_mode": "cancel",
            },
        }

    def action_submit_for_verification(self):
        self.ensure_one()

        if self.status != "in_progress":
            raise ValidationError(_("Only In Progress CIs can be submitted."))

        if not self.date_due:
            raise ValidationError(_("Please set a Due Date first."))

        if self._get_open_verification_activity():
            raise ValidationError(_("Closure activity already exists."))

        assignee = self._get_verification_assignee()
        today = fields.Date.context_today(self)
        due_date = today + timedelta(days=14)
        reference = self.action_reference or self.display_name
        summary = _("%s Review for Effectiveness") % reference

        return {
            "type": "ir.actions.act_window",
            "name": _("Submit for Closure Review"),
            "res_model": "adi_improvement_app.ci_submit_review_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_ci_id": self.id,
                "default_reviewer_id": assignee.id,
                "default_due_date": due_date,
                "default_summary": summary,
            },
        }

    def action_open_verification_wizard(self):
        self.ensure_one()

        if self.status != "awaiting_verification":
            raise ValidationError(
                _("Closure status can only be updated from Awaiting Closure.")
            )
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.action_reference} - Closure Status",
            "res_model": "adi_improvement_app.ci_verification_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_ci_id": self.id,
                "default_verification_result": self.verification_result,
                "default_closure_statement": self.closure_statement,
                "closure_mode": "verification",
            },
        }

    def action_reopen(self):
        verification_type = self._get_review_activity_type()
        rework_type = self._get_rework_activity_type()

        for rec in self:
            open_activities = rec.activity_ids.filtered(
                lambda a: a.activity_type_id in (verification_type, rework_type)
            )

            if open_activities:
                open_activities.with_context(bypass_locked_workflow_activity=True).write({"note": False})
                open_activities.with_context(bypass_locked_workflow_activity=True).action_feedback(feedback="")

            rec.write({
                "status": "in_progress",
                "ci_date_done": False,
                "verified_by": False,
                "date_submitted_for_verification": False,
                "verification_result": False,
                # keep closure_statement
            })

            rec.message_post(
                body=_("CI reopened by %s on %s. Status reset to In Progress.")
                % (
                    self.env.user.name,
                    fields.Date.context_today(rec).strftime("%d %b %Y"),
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("action_reference"):
                vals["action_reference"] = self.env["ir.sequence"].next_by_code(
                    "adi_improvement_app.ci.sequence"
                ) or "CI0000"
        return super().create(vals_list)


class CiVerificationWizard(models.TransientModel):
    _name = "adi_improvement_app.ci_verification_wizard"
    _description = "CI Verification Wizard"

    ci_id = fields.Many2one(
        "adi_improvement_app.improvement",
        required=True,
        ondelete="cascade",
    )
    verification_result = fields.Selection(CI_VERIFICATION_RESULT, required=True, string = "Result")
    closure_statement = fields.Text(required=True)

    available_result_options = fields.Char(compute="_compute_available_result_options")

    @api.depends_context("closure_mode")
    def _compute_available_result_options(self):
        for rec in self:
            mode = rec.env.context.get("closure_mode")
            if mode == "cancel":
                rec.available_result_options = "abort"
            else:
                rec.available_result_options = "achieved,further_action"

    def action_confirm(self):
        self.ensure_one()
        ci = self.ci_id
        closure_mode = self.env.context.get("closure_mode")
        activity = ci._get_open_verification_activity()

        ci.closure_statement = self.closure_statement
        ci.verification_result = self.verification_result

        if closure_mode == "cancel":
            if self.verification_result != "abort":
                raise ValidationError(
                    _("Only 'Not implemented' can be used when cancelling a CI.")
                )

            ci.status = "closed"
            ci.verified_by = self.env.user
            if not ci.ci_date_done:
                ci.ci_date_done = fields.Date.context_today(ci)

            ci.date_submitted_for_verification = False

            ci.message_post(
                body=_("%s closed without implementation")
                % (ci.action_reference or ci.display_name)
            )

        else:
            if ci.status != "awaiting_verification":
                raise ValidationError(
                    _("Closure outcome can only be recorded from Awaiting Closure.")
                )

            if self.verification_result in ("achieved", "abort"):
                ci.status = "closed"
                ci.verified_by = self.env.user
                if not ci.ci_date_done:
                    ci.ci_date_done = fields.Date.context_today(ci)

                if activity:
                    activity.with_context(bypass_locked_workflow_activity=True).write({"note": False})
                    activity.with_context(bypass_locked_workflow_activity=True).action_feedback(feedback="")

                if self.verification_result == "abort":
                    ci.message_post(
                        body=_("%s closed without implementation")
                        % (ci.action_reference or ci.display_name)
                    )

            else:
                ci.status = "in_progress"
                ci.ci_date_done = False
                ci.verified_by = False
                ci.date_submitted_for_verification = False
                #ci.verification_counter += 1

                if activity:
                    activity.with_context(bypass_locked_workflow_activity=True).write({"note": False})
                    activity.with_context(bypass_locked_workflow_activity=True).action_feedback(feedback="")

                ci._create_rework_activity(self.closure_statement)

                ci.message_post(
                    body=_("%s Additional work required. Returned to In Progress")
                    % (ci.action_reference or ci.display_name)
                )

        return {"type": "ir.actions.act_window_close"}
    
class CiSubmitReviewWizard(models.TransientModel):
    _name = "adi_improvement_app.ci_submit_review_wizard"
    _description = "Submit CI for Closure Review"

    ci_id = fields.Many2one(
        "adi_improvement_app.improvement",
        required=True,
        ondelete="cascade",
    )
    reviewer_id = fields.Many2one(
        "res.users",
        string="Reviewer",
        readonly=True,
        required=True,
    )
    due_date = fields.Date(
        string="Due Date",
        readonly=True,
        required=True,
    )
    summary = fields.Char(
        string="Summary",
        readonly=True,
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()
        ci = self.ci_id

        if ci.status != "in_progress":
            raise ValidationError(_("Only In Progress CIs can be submitted."))

        if not ci.date_due:
            raise ValidationError(_("Please set a Due Date first."))

        if ci._get_open_verification_activity():
            raise ValidationError(_("Closure activity already exists."))

        ci._close_open_rework_activity()

        activity_type = ci._get_review_activity_type()
        today = fields.Date.context_today(ci)
        note = _(
            "%s has been submitted for closure by %s: %s"
        ) % (
            ci.action_reference or ci.display_name,
            self.env.user.name,
            today.strftime("%d %b %Y"),
        )

        ci._create_controlled_activity(
            activity_type=activity_type,
            user=self.reviewer_id,
            due_date=self.due_date,
            summary=self.summary,
            note=note,
        )

        ci.write({
            "status": "awaiting_verification",
            "date_submitted_for_verification": today,
        })

        ci.message_post(
            body=_(
                "CI submitted for Effectiveness Review by %s on %s. "
                "Review activity assigned to %s with due date %s."
            ) % (
                self.env.user.name,
                today.strftime("%d %b %Y"),
                self.reviewer_id.name,
                self.due_date.strftime("%d %b %Y") if self.due_date else "",
            )
        )
        return {"type": "ir.actions.act_window_close"}