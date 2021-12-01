from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    # Inherited methods
    def _adjust_procure_method(self):
        """
            Inherited so that in case of direct MO creation it changes the procure_method,
            on the basis of the forecasted quantity.
        """
        for move in self:
            if move.product_id.virtual_available < move.product_qty:
                if move.product_uom_qty > move.product_id.virtual_available:
                    move.procure_method = 'make_to_order'
            else:
                super(StockMove, self)._adjust_procure_method()
