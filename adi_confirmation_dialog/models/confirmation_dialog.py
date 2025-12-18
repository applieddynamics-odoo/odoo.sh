from odoo import models, fields

class AdiConfirmationDialog(models.TransientModel):
    _name = 'adi.confirmation.dialog'
    _description = 'Custom Confirmation Dialog'

    title = fields.Char(readonly=True)
    message = fields.Html(readonly=True)

    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    callback_method = fields.Char(required=True)

    def action_confirm(self):
        self.ensure_one()
        record = self.env[self.res_model].browse(self.res_id)
        if record and hasattr(record, self.callback_method):
            getattr(record, self.callback_method)()
        return {'type': 'ir.actions.act_window_close'}
