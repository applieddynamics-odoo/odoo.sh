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

        def action_mark_complete(self):
            self.ensure_one()

            if self.x_adi_completed:
                return True

            return {
                "type": "ir.actions.act_window",
                "name": "Complete Sales Order",
                "res_model": "sale.order.complete.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_order_id": self.id,
                },
            }


            order.message_post(body=_("Sales Order marked <b>Completed</b>."))
