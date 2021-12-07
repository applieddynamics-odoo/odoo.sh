from odoo import api, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    # Inherited methods
    @api.model
    def _run_pull(self, procurements):
        """
            Inherited to call run_buy and _run_manufacture in some cases.
            By changing the procure_method.
        """
        for procurement, rule in procurements:
            requested_quantity = procurement.product_uom._compute_quantity(procurement.product_qty,
                                                                           procurement.product_id.uom_id)
            product_virtual_quantity = procurement.product_id.virtual_available if procurement.product_id.virtual_available > 0 else 0
            needed_quantity = requested_quantity - product_virtual_quantity if requested_quantity > product_virtual_quantity else 0
            if needed_quantity:
                rule.procure_method = 'make_to_order'
        super(StockRule, self)._run_pull(procurements)

    @api.model
    def _run_buy(self, procurements):
        """
            Inherited the method to consider forecast quantity for a product,
            while making new Purchase order from sale order.
        """
        filtered_procurements = self.filter_procurements_on_forecast_qty(procurements=procurements)
        if filtered_procurements:
            super(StockRule, self)._run_buy(filtered_procurements)

    @api.model
    def _run_manufacture(self, procurements):
        """
            Inherited the method to consider forecast quantity for a product,
            while making new MTO order from sale order.
        """
        filtered_procurements = self.filter_procurements_on_forecast_qty(procurements=procurements)
        if filtered_procurements:
            super(StockRule, self)._run_manufacture(filtered_procurements)

    def _update_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, line):
        """
            Inherited the method to make the changes in the value of the quantity,
            while changing the existing Purchase order from sale order.
        """
        res = super(StockRule, self)._update_purchase_order_line(product_id, product_qty, product_uom,
                                                                 company_id, values, line)
        requested_quantity = product_uom._compute_quantity(product_qty, product_id.uom_id)
        qty_from_po = line.product_qty
        product_virtual_available = product_id.virtual_available if product_id.virtual_available > 0 else 0
        needed_quantity = requested_quantity - product_virtual_available if requested_quantity > product_virtual_available else 0
        if needed_quantity:
            res['product_qty'] = needed_quantity + qty_from_po
        return res

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values,
                         bom):
        """
            Inherited so that we can change the quantity of the quantity of the MTO
            on the basis of forecasted quantity.
        """
        res = super(StockRule, self)._prepare_mo_vals(product_id, product_qty, product_uom, location_id, name,
                                                      origin, company_id, values, bom)
        requested_quantity = product_uom._compute_quantity(product_qty, product_id.uom_id)
        product_virtual_quantity = product_id.virtual_available if product_id.virtual_available > 0 else 0
        needed_quantity = requested_quantity - product_virtual_quantity if requested_quantity > product_virtual_quantity else 0
        if needed_quantity:
            res['product_qty'] = needed_quantity
        return res

    # Custom or business methods
    def filter_procurements_on_forecast_qty(self, procurements):
        """
            To filter out the procurements with the forecasted quantity for buy or mto route.
        """
        procurements_to_be_considered = []
        for procurement, rule in procurements:
            requested_quantity = procurement.product_uom._compute_quantity(procurement.product_qty,
                                                                           procurement.product_id.uom_id)
            product_virtual_quantity = procurement.product_id.virtual_available if procurement.product_id.virtual_available > 0 else 0
            needed_quantity = requested_quantity - product_virtual_quantity if requested_quantity > product_virtual_quantity else 0
            if needed_quantity:
                procurements_to_be_considered.append([procurement, rule])
        return procurements_to_be_considered
