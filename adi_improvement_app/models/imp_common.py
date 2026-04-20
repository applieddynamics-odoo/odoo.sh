from odoo import fields, models, api

#-------------------------------------------------------------
# Constants
#-------------------------------------------------------------

PROCESS_AREA = [
    ("Proposals and Contracts", "Proposals and Contracts"),
    ("Systems Engineering", "Systems Engineering"),
    ("Software Engineering", "Software Engineering"),
    ("Production", "Production"),
    ("Purchasing/Shipping/Receiving", "Purchasing/Shipping/Receiving"),
    ("Support Services", "Support Services"),
]

#-------------------------------------------------------------
# Class and field definition (shared by CI and CAR models)
#-------------------------------------------------------------
class ImpCommon(models.AbstractModel):
    _name = "adi_improvement_app.imp_common"
    _description = "Improvement Common Fields"

# Legacy employee field to maintain history and allow for reporting on legacy data. New records should use owner_id instead of this field.
    owner_employee_id = fields.Many2one(
        "hr.employee",
        string="Owner (Legacy Employee)",
        index=True,
        ondelete="set null",
    )

    process_area = fields.Selection(PROCESS_AREA)
    owner_id = fields.Many2one(
        "res.users",
        string="Owner",
        index=True,
        ondelete="set null",
    )
    title = fields.Char(required=True, tracking=True)
    action_reference = fields.Char(string="Reference", readonly=False, copy=False, index=True)
        # Combine date opened and opened by in the form to save space 
    #date_opened = fields.Date(default=fields.Date.context_today, tracking=False)
    date_opened = fields.Date(default=fields.Date.today)
    opened_by = fields.Many2one("res.users", default=lambda self: self.env.user)

    date_opened_display = fields.Char(
        string="Date Opened",
        compute="_compute_date_opened_display",
        readonly=False,
    )

    @api.depends("date_opened", "opened_by")
    def _compute_date_opened_display(self):
        for rec in self:
            rec.date_opened_display = ""
            if rec.date_opened and rec.opened_by:
                rec.date_opened_display = "%s by %s" % (
                    rec.date_opened.strftime("%d %b %Y"),
                    rec.opened_by.name,
                )
            elif rec.date_opened:
                rec.date_opened_display = rec.date_opened.strftime("%d %b %Y")


    legacy_model = fields.Char(readonly=False, index=True)
    legacy_id = fields.Integer(readonly=False, index=True)
    legacy_ref = fields.Char(readonly=False)