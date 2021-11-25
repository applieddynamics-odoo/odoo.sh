from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Inherited method
    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values,
                                                      po):
        """
            Inherited the method to make the changes in the value of the quantity,
            while making new Purchase order from sale order.
        """
        res = super(SaleOrderLine, self)._prepare_purchase_order_line_from_procurement(product_id, product_qty,
                                                                                       product_uom, company_id, values,
                                                                                       po)
        is_from_sale = bool(values.get('group_id').sale_id) if values.get('group_id') else False
        if is_from_sale:
            needed_quantity = product_qty - product_id.virtual_available if product_qty > product_id.virtual_available else 0
            if needed_quantity:
                res['product_qty'] = needed_quantity
        return res
