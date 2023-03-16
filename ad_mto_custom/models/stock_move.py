from odoo import models, fields


class StockMove(models.Model):
    _inherit = "stock.move"

    # Field declarations
    quantity_already_processed = fields.Float(
        string="Quantity already processed")
    reassign_by_mo_id = fields.Many2one('mrp.production',
                                        string='Reassign by MO')

    # Inherited methods
    def _adjust_procure_method(self):
        """
            Inherited so that in case of direct MO creation it changes the procure_method,
            on the basis of the forecasted quantity.
        """
        for move in self:
            product_id = move.product_id
            domain = [('location_src_id', '=', move.location_id.id),
                      ('location_dest_id', '=', move.location_dest_id.id),
                      ('action', '!=', 'push')]
            packaging_id = move.product_packaging_id
            rules = self.env['procurement.group']._search_rule(
                False, packaging_id, product_id, move.warehouse_id, domain)
            if rules:
                requested_quantity = move.product_uom._compute_quantity(
                    move.product_uom_qty, move.product_id.uom_id)
                product_virtual_quantity = move.product_id.virtual_available if move.product_id.virtual_available > 0 else 0
                quantity_already_processed_move = move.quantity_already_processed
                if quantity_already_processed_move:
                    if requested_quantity > quantity_already_processed_move:
                        move.procure_method = 'make_to_order'
                else:
                    if requested_quantity > product_virtual_quantity:
                        move.procure_method = 'make_to_order'
                    else:
                        super()._adjust_procure_method()
            else:
                move.procure_method = 'make_to_stock'
