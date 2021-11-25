from odoo import api, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    # Inherited methods
    @api.model
    def _run_buy(self, procurements):
        """
            Inherited the method to consider forecast quantity for a product,
            while making new Purchase order from sale order.
        """
        is_from_sale = self.check_procurements_are_from_sale(procurements)
        if is_from_sale:
            filtered_procurements = self.filter_procurements_on_forecast_qty(procurements=procurements)
            if filtered_procurements:
                super(StockRule, self)._run_buy(filtered_procurements)
        else:
            super(StockRule, self)._run_buy(procurements)

    @api.model
    def _run_manufacture(self, procurements):
        """
            Inherited the method to consider forecast quantity for a product,
            while making new MTO order from sale order.
        """
        is_from_sale = self.check_procurements_are_from_sale(procurements)
        if is_from_sale:
            filtered_procurements = self.filter_procurements_on_forecast_qty(procurements=procurements)
            if filtered_procurements:
                super(StockRule, self)._run_manufacture(filtered_procurements)
        else:
            super(StockRule, self)._run_manufacture(procurements)

    def _update_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, line):
        """
            Inherited the method to make the changes in the value of the quantity,
            while changing the existing Purchase order from sale order.
        """
        res = super(StockRule, self)._update_purchase_order_line(product_id, product_qty, product_uom,
                                                                 company_id, values, line)
        is_from_sale = bool(values.get('group_id').sale_id) if values.get('group_id') else False
        if is_from_sale:
            qty_from_po = res['product_qty'] - line.product_qty
            needed_quantity = line.product_qty - product_id.virtual_available if line.product_qty > product_id.virtual_available else 0
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
        is_from_sale = bool(values.get('group_id').sale_id) if values.get('group_id') else False
        if is_from_sale:
            needed_quantity = product_qty - product_id.virtual_available if product_qty > product_id.virtual_available else 0
            if needed_quantity:
                res['product_qty'] = needed_quantity
        return res

    # Custom or business methods
    def filter_procurements_on_forecast_qty(self, procurements):
        """
            To filter out the procurements with the forecasted quantity for buy or mto route.
        """
        procurements_to_be_considered = []
        for procurement in procurements:
            needed_quantity = procurement[0].product_qty - procurement[0].product_id.virtual_available \
                if procurement[0].product_qty > procurement[0].product_id.virtual_available else 0
            if needed_quantity:
                procurements_to_be_considered.append(procurement)
        return procurements_to_be_considered

    def check_procurements_are_from_sale(self, procurements):
        """
            Check if the procurements are from sale_order.
        """
        is_from_sale = False
        for procurement in procurements:
            sale_group_id = procurement[0].values.get('group_id').sale_id
            is_from_sale = bool(sale_group_id)
            if is_from_sale:
                break
        return is_from_sale
