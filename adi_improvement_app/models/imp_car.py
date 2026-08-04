from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

# -------------------------------------------------------------
# Constants
# -------------------------------------------------------------

SOURCE = [
    ("Internal Audit Finding", "Internal Audit Finding"),
    ("External Audit Finding", "External Audit Finding"),
    ("Customer Compliant/Issue", "Customer Compliant/Issue"),
    ("Product/Service Nonconformity", "Product/Service Nonconformity"),
    ("Supplier Nonconformity", "Supplier Nonconformity"),
    ("Process Failure (Internal)", "Process Failure (Internal)"),
    ("Regulatory/Compliance Issue", "Regulatory/Compliance Issue"),
]

STATUS = [
    ("open", "Open"),
    ("containment", "Containment (In Progress)"),
    ("awaiting_verification", "Done - Awaiting Verification"),
    ("closed", "Closed"),
]

OCCURRENCE = [("first", "First"), ("repeat", "Repeat")]
RISK = [("low", "Low"), ("medium", "Medium"), ("high", "High")]


# -------------------------------------------------------------
# Main CAR Class and field declarations
# -------------------------------------------------------------

class CiCar(models.Model):
    _name = "adi_improvement_app.car"
    _description = "Corrective Action Report (CAR)"
    _rec_name = "action_reference"
    _inherit = ["adi_improvement_app.imp_common", "mail.thread", "mail.activity.mixin"]

    owner = fields.Char(string="Owner (legacy)")

    status = fields.Selection(STATUS, default="open")
    source = fields.Selection(SOURCE)
    occurrence = fields.Selection(OCCURRENCE, default="")
    risk = fields.Selection(RISK, tracking=True)

    summary = fields.Text()

    containment = fields.Text()
    cause = fields.Text()
    car_actions = fields.Text()

    date_in_progress = fields.Date(string="Date In Progress")
    est_verify_end_date = fields.Date(string="Estimated Date")
    date_closed = fields.Date(string="Closed Date")

    verified_by = fields.Many2one("res.users", string="Verified By", readonly=False)
    
    verification_plan = fields.Text(
        string="Verification Plan",
        help="Planned approach to verify effectiveness (method, checks, responsibilities)."
    )
    
    verification_notes = fields.Text(
        string="Verification Evidence",
        placeholder="Objective evidence gathered during verification, findings and review notes..."
    )

    car_date_done = fields.Date(
        string="Containment Done Date",
        readonly=False,
    )

    target_contained_date = fields.Date(
        compute="_compute_target_contained_date",
        store=True,
        readonly=False,
    )

    target_contained_date_display = fields.Char(
        string="Due Date",
        compute="_compute_target_contained_date_display",
        readonly=False,
    )

    est_verify_end_date_display = fields.Char(
        string="Verification Target Display",
        compute="_compute_est_verify_end_date_display",
    )

    related_so = fields.Many2one("sale.order", tracking=True)
    related_so_customer = fields.Char(string="Customer (legacy)")
    related_so_description = fields.Char()

    customer_company_id = fields.Many2one(
        "res.partner",
        string="Customer",
        domain=[("is_company", "=", True)],
        index=True,
        ondelete="set null",
    )

    verification_counter = fields.Integer(
        string="Verification fails",
        default=0,
        readonly=True,
    )

    related_so_applicable = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],
        string="Related Sales Order?",
        default="no",
    )

    # Actions ----------------------------------------------------

    def action_start_containment(self):
        for rec in self:
            if not rec.risk:
                raise ValidationError("Please select a Risk before starting containment.")
            if not rec.related_so_applicable:
                raise ValidationError("Please confirm whether there is a Related Sales Order before starting containment.")
            if rec.related_so_applicable == "yes" and not rec.related_so:
                raise ValidationError("Please select the Related Sales Order before starting containment.")

            rec.status = "containment"
            if not rec.date_in_progress:
                rec.date_in_progress = fields.Date.context_today(rec)

    def action_open_verification_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.action_reference} - Plan Verification",
            "res_model": "adi_improvement_app.containment_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_car_id": self.id,
            },
        }

    def action_reopen(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Reopen CAR",
            "res_model": "adi_improvement_app.reopen_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_car_id": self.id,
            },
        }

    def action_open_close_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.action_reference} - Update Verification status",
            "res_model": "adi_improvement_app.close_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_car_id": self.id,
                "default_verification_notes": self.verification_notes,
            },
        }

    def _risk_days(self):
        self.ensure_one()
        return {"low": 120, "medium": 90, "high": 30}.get(self.risk, 0)

    @api.depends("risk", "date_in_progress")
    def _compute_target_contained_date(self):
        for rec in self:
            if not rec.date_in_progress or not rec.risk:
                rec.target_contained_date = False
                continue
            rec.target_contained_date = rec.date_in_progress + relativedelta(days=rec._risk_days())

    @api.depends("target_contained_date", "car_date_done", "status")
    def _compute_target_contained_date_display(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.target_contained_date_display = ""

            if not rec.target_contained_date:
                continue

            target = rec.target_contained_date
            target_txt = target.strftime("%d %b %Y")

            if rec.status in ("awaiting_verification", "closed") and rec.car_date_done:
                done = rec.car_date_done
                done_txt = done.strftime("%d %b %Y")
                delta = (done - target).days

                if delta <= 0:
                    rec.target_contained_date_display = (
                        f"Completed on time on {done_txt}. "
                        f"(Target : {target_txt})"
                    )
                else:
                    rec.target_contained_date_display = (
                        f"Completed {delta} days late on {done_txt}. "
                        f"(Target : {target_txt})"
                    )
                continue

            delta = (target - today).days
            if delta > 0:
                rec.target_contained_date_display = f"Target: {target_txt} ({delta} days remaining)"
            elif delta == 0:
                rec.target_contained_date_display = f"Target: {target_txt} (due today)"
            else:
                rec.target_contained_date_display = f"Target: {target_txt} (overdue by {abs(delta)} days)"

    @api.depends("est_verify_end_date", "date_closed", "status")
    def _compute_est_verify_end_date_display(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.est_verify_end_date_display = ""

            if not rec.est_verify_end_date:
                continue

            target = rec.est_verify_end_date
            target_txt = target.strftime("%d %b %Y")

            if rec.status == "closed" and rec.date_closed:
                done = rec.date_closed
                done_txt = done.strftime("%d %b %Y")
                delta = (done - target).days

                if delta <= 0:
                    rec.est_verify_end_date_display = (
                        f"Completed on time on {done_txt}. "
                        f"(Target : {target_txt})"
                    )
                else:
                    rec.est_verify_end_date_display = (
                        f"Completed {delta} days late on {done_txt}. "
                        f"(Target : {target_txt})"
                    )
                continue

            delta = (target - today).days
            if delta > 0:
                rec.est_verify_end_date_display = f"Target: {target_txt} ({delta} days remaining)"
            elif delta == 0:
                rec.est_verify_end_date_display = f"Target: {target_txt} (due today)"
            else:
                rec.est_verify_end_date_display = f"Target: {target_txt} (overdue by {abs(delta)} days)"

    @api.constrains("occurrence", "risk")
    def _check_repeat_risk(self):
        for rec in self:
            if rec.occurrence == "repeat" and rec.risk == "low":
                raise ValidationError("Repeat occurrences cannot be marked as Low risk.")
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("action_reference"):
                vals["action_reference"] = self.env["ir.sequence"].next_by_code("adi_improvement_app.car.sequence") or "CA0000"
        return super().create(vals_list)
        
    # Related Sales Order logic 

    @api.onchange("related_so")
    def _onchange_related_so_set_customer(self):
        for rec in self:
            if rec.related_so:
                rec.related_so_applicable = "yes"
                if rec.related_so.partner_id:
                    rec.customer_company_id = rec.related_so.partner_id

    @api.constrains("related_so_applicable", "related_so")
    def _check_related_so_required(self):
        for rec in self:
            if rec.related_so_applicable == "yes" and not rec.related_so:
                raise ValidationError(
                    "Please select a Related SO when 'Related Sales Order?' is Yes."
                )
            
