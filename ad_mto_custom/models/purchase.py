from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Inherited method
    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id,
                                                      product_qty, product_uom,
                                                      company_id, values, po):
        """
            Inherited the method to make the changes in the value of the quantity,
            while making new Purchase order from sale order.
        """
        res = super()._prepare_purchase_order_line_from_procurement(
                        product_id, product_qty, product_uom, company_id,
                        values, po)
        requested_quantity = product_uom._compute_quantity(
            product_qty, product_id.uom_id)
        move_from_procurement = values.get('move_dest_ids')
        quantity_already_processed_move = sum(
            move_from_procurement.mapped('quantity_already_processed'))
        if quantity_already_processed_move:
            if requested_quantity > quantity_already_processed_move:
                res['product_qty'] = requested_quantity - quantity_already_processed_move
        else:
            product_virtual_quantity = product_id.virtual_available if product_id.virtual_available > 0 else 0
            needed_quantity = requested_quantity - product_virtual_quantity if requested_quantity > product_virtual_quantity else 0
            if needed_quantity:
                res['product_qty'] = needed_quantity
        return res
