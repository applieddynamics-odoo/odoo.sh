from odoo import fields, models

class DisposeConfirmWizard(models.TransientModel):
    _name = "adi.dispose.confirm.wizard"
    _description = "Confirm Disposal"

    record_id = fields.Many2one(
        comodel_name="x_facility_checks",
        required=True,
        readonly=True,
    )

    def action_yes(self):
        self.ensure_one()
        rec = self.record_id

        rec.write({'x_studio_selection_field_387_1jaj511eb': 'status4'})

        rec.message_post(
            body=(
                "Please confirm that the shelf life item has been suitably disposed: "
                "<b>YES</b><br/>"
                f"Confirmed by: {self.env.user.name}"
            ),
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )
        return {"type": "ir.actions.act_window_close"}

    def action_no(self):
        return {"type": "ir.actions.act_window_close"}

