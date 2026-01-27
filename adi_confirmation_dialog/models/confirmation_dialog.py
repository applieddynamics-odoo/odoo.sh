from odoo import fields, models
from markupsafe import Markup


class AdiConfirmationDialog(models.TransientModel):
    _name = "adi.confirmation.dialog"
    _description = "ADI Confirmation Dialog"

    # Single-record targeting
    res_model = fields.Char(required=True, readonly=True)
    res_id = fields.Integer(required=True, readonly=True)

    # UI text (HTML allowed)
    message_html = fields.Html(string="Message", sanitize=False, required=True, readonly=True)

    # Server action to run when user clicks Yes
    yes_server_action_id = fields.Many2one(
        "ir.actions.server",
        string="Yes Server Action",
        required=True,
        readonly=True,
    )

    # Optional chatter logging
    log_to_chatter = fields.Boolean(default=False, readonly=True)
    append_confirmed_line = fields.Boolean(default=True, readonly=True)
    chatter_note_html = fields.Html(string="Chatter Note", sanitize=False, readonly=True)

    def _get_record(self):
        self.ensure_one()
        return self.env[self.res_model].browse(self.res_id).exists()

    def action_yes(self):
        self.ensure_one()
        rec = self._get_record()
        if not rec:
            return {"type": "ir.actions.act_window_close"}

        # Run the server action as if triggered from this record
        ctx = dict(self.env.context or {})
        ctx.update({
            "active_model": self.res_model,
            "active_id": rec.id,
            "active_ids": [rec.id],
        })
        self.yes_server_action_id.with_context(ctx).run()

        # Optional chatter note
        if self.log_to_chatter and hasattr(rec, "message_post"):
            disposed_date = fields.Date.context_today(self)
            disposed_date_str = disposed_date.strftime("%d %b %Y")

            base_note = (self.chatter_note_html or "").strip() or (self.message_html or "").strip()

            if self.append_confirmed_line:
                body = Markup(
                    f"{base_note}<br/>"
                    f"Confirmed on {disposed_date_str} by: {self.env.user.name}"
                )
            else:
                body = Markup(base_note)

            rec.message_post(
                body=body,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )

        return {"type": "ir.actions.act_window_close"}

    def action_no(self):
        return {"type": "ir.actions.act_window_close"}
