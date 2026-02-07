# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_adi_completed = fields.Boolean(string="Completed", default=False, copy=False, tracking=True)
    x_adi_completed_on = fields.Datetime(string="Completed On", copy=False, tracking=True)
    x_adi_completed_by = fields.Many2one("res.users", string="Completed By", copy=False, tracking=True)
    x_adi_completion_notes = fields.Text(string="Completion Notes", copy=False)

    def action_open_complete_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Mark Complete"),
            "res_model": "sale.order.complete.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_sale_order_id": self.id,
            },
        }

    def action_mark_completed(self, notes=False):
        for order in self:
            if order.x_adi_completed:
                continue
            order.write({
                "x_adi_completed": True,
                "x_adi_completed_on": fields.Datetime.now(),
                "x_adi_completed_by": self.env.user.id,
                "x_adi_completion_notes": notes or False,
            })
            order.message_post(body=_("Sales Order marked <b>Completed</b>."))
