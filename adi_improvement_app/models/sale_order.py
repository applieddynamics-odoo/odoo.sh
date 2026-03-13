from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_studio_sales_description = fields.Char(string="Sales Description")
