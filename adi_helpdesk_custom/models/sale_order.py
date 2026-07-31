from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("name", "x_studio_sales_description")
    @api.depends_context("adi_helpdesk_charge_to")
    def _compute_display_name(self):
        super()._compute_display_name()

        if not self.env.context.get("adi_helpdesk_charge_to"):
            return

        for order in self:
            description = (
                order.x_studio_sales_description or ""
            ).strip()

            if description:
                order.display_name = (
                    f"{order.name} : {description}"
                )
            else:
                order.display_name = order.name