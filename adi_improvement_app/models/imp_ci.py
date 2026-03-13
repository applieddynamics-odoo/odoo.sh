from odoo import api, fields, models
from odoo.exceptions import ValidationError

SOURCE = [
    ("Internal Audit Finding", "Internal Audit Finding"),
    ("External Audit Finding", "External Audit Finding"),
    ("Customer Request", "Customer Request"),
    ("Internal Opportunity Identified", "Internal Opportunity Identified"),
    ("Lessons Learnt", "Lessons Learnt"),
    ("Corrective Action Report (CAR)", "Corrective Action Report (CAR)"),
]

PRIORITY = [("low", "Low"), ("medium", "Medium"), ("high", "High")]

STATUS = [
    ("open", "Open"),
    ("in_progress", "In Progress"),
    ("on_hold", "On Hold"),
    ("awaiting_verification", "Awaiting Verification"),
    ("closed", "Closed"),
]

CI_VERIFICATION_RESULT = [
    ("achieved", "Achieved Intended Improvement"),
    ("further_action", "Further Action Required"),
]


class CiImprovement(models.Model):
    _name = "adi_improvement_app.improvement"
    _description = "Continuous Improvement"
    _rec_name = "action_reference"
    _inherit = ["adi_improvement_app.imp_common", "mail.thread", "mail.activity.mixin"]

    status = fields.Selection(STATUS, default="open")
    source = fields.Selection(SOURCE)
    priority = fields.Selection(PRIORITY, default="")
    owner = fields.Char(string="Owner (legacy)")
    summary = fields.Text()
    notes = fields.Text()
    actions = fields.Text()
    date_due = fields.Date()

    date_in_progress = fields.Date(
        string="Date In Progress",
        readonly=False,
    )

    date_submitted_for_verification = fields.Date(
        string="Submitted for Verification",
        readonly=False,
    )

    ci_date_done = fields.Date(string="CI Done Date", readonly=False)
    verified_by = fields.Many2one("res.users", string="Verified By", readonly=False)
    verification_result = fields.Selection(CI_VERIFICATION_RESULT, readonly=True)
    closure_statement = fields.Text()
    verification_counter = fields.Integer(string="Verification fails", default=0, readonly=True)

    def action_set_in_progress(self):
        for rec in self:
            if not rec.date_due:
                raise ValidationError(
                    "Please set a Due Date before setting this CI to In Progress."
                )

            rec.status = "in_progress"
            if not rec.date_in_progress:
                rec.date_in_progress = fields.Date.context_today(rec)

            rec.message_post(
                body="CI moved to In Progress by %s on %s."
                    % (self.env.user.name, fields.Date.context_today(rec).strftime("%d %b %Y"))
            )

    def action_set_on_hold(self):
        for rec in self:
            rec.status = "on_hold"
            rec.message_post(
                body="CI placed On Hold by %s on %s."
                    % (self.env.user.name, fields.Date.context_today(rec).strftime("%d %b %Y"))
            )

    def action_submit_for_verification(self):
        for rec in self:
            if rec.status != "in_progress":
                raise ValidationError(
                    "Only CIs in progress can be submitted for verification."
                )

            rec.status = "awaiting_verification"
            rec.date_submitted_for_verification = fields.Date.context_today(rec)

            rec.message_post(
                body="CI submitted for Verification by %s on %s."
                    % (self.env.user.name, fields.Date.context_today(rec).strftime("%d %b %Y"))
            )

    def action_open_verification_wizard(self):
        self.ensure_one()
        if self.status != "awaiting_verification":
            raise ValidationError("Verification status can only be updated from Awaiting Verification.")
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.action_reference} - Verification Status",
            "res_model": "adi_improvement_app.ci_verification_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_ci_id": self.id,
                "default_verification_result": self.verification_result,
                "default_closure_statement": self.closure_statement,
            },
        }

    def action_reopen(self):
        for rec in self:
            rec.write({
                "status": "in_progress",
                "ci_date_done": False,
                "verified_by": False,
            })
            rec.message_post(
                body="CI reopened by %s on %s. Status reset to In Progress."
                    % (self.env.user.name, fields.Date.context_today(rec).strftime("%d %b %Y"))
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

    ci_id = fields.Many2one("adi_improvement_app.improvement", required=True, ondelete="cascade")
    verification_result = fields.Selection(CI_VERIFICATION_RESULT, required=True)
    closure_statement = fields.Text(required=True)

    def action_confirm(self):
        self.ensure_one()
        ci = self.ci_id

        if ci.status != "awaiting_verification":
            raise ValidationError("Verification outcome can only be recorded from Awaiting Verification.")

        ci.closure_statement = self.closure_statement
        ci.verification_result = self.verification_result

        if self.verification_result == "achieved":
            ci.status = "closed"
            ci.verified_by = self.env.user
            if not ci.ci_date_done:
                ci.ci_date_done = fields.Date.today()
                ci.message_post(
                    body="CI verified as achieved by %s on %s."
                        % (self.env.user.name, fields.Date.context_today(ci).strftime("%d %b %Y"))
                )

        else:
            ci.status = "in_progress"
            ci.ci_date_done = False
            ci.verified_by = False
            ci.date_submitted_for_verification = False
            ci.verification_counter += 1
            ci.message_post(
                body="CI verification recorded as Further Action Required by %s on %s. Record returned to In Progress."
                    % (self.env.user.name, fields.Date.context_today(ci).strftime("%d %b %Y"))
            )



        return {"type": "ir.actions.act_window_close"}