from odoo import api, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_buy(self, procurements):
        """
            Inherited the method to consider forecast quantity for a product,
            while making new Purchase order from sale order.
        """
        filtered_procurements = self.filter_procurements_on_forecast_qty(procurements=procurements)
        if filtered_procurements:
            super()._run_buy(filtered_procurements)

    @api.model
    def _run_manufacture(self, procurements):
        """
            Inherited the method to consider forecast quantity for a product,
            while making new MTO order from sale order.
        """
        filtered_procurements = self.filter_procurements_on_forecast_qty(procurements=procurements)
        if filtered_procurements:
            super()._run_manufacture(filtered_procurements)

    def _update_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, line):
        """
            Inherited the method to make the changes in the value of the quantity,
            while changing the existing Purchase order from sale order.
        """
        res = super()._update_purchase_order_line(product_id, product_qty, product_uom,
                                                                 company_id, values, line)
        product_virtual_available = product_id.virtual_available if product_id.virtual_available > 0 else 0
        requested_quantity = product_uom._compute_quantity(product_qty, product_id.uom_id)
        qty_from_po = abs(line.product_qty)
        move_from_procurement = values.get('move_dest_ids')
        rerun_quantity_data = self.calculate_qty_for_rerun_move(move_from_procurement,
                                                                requested_quantity)
        if bool(rerun_quantity_data):
            res['product_qty'] = requested_quantity - rerun_quantity_data.get('previous_quantity') + qty_from_po
            move_from_procurement.quantity_already_processed = requested_quantity
        else:
            needed_quantity = requested_quantity - product_virtual_available if requested_quantity > product_virtual_available else 0
            if needed_quantity:
                res['product_qty'] = res['product_qty'] + qty_from_po
                if len(move_from_procurement) > 1:
                    for move in move_from_procurement:
                        move.quantity_already_processed = move.product_uom_qty
                else:
                    move_from_procurement.quantity_already_processed = needed_quantity
        return res

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values,
                         bom):
        """
            Inherited so that we can change the quantity of the quantity of the MTO
            on the basis of forecasted quantity.
        """
        res = super()._prepare_mo_vals(product_id, product_qty, product_uom, location_id, name,
                                                      origin, company_id, values, bom)
        product_virtual_quantity = product_id.virtual_available if product_id.virtual_available > 0 else 0
        requested_quantity = product_uom._compute_quantity(product_qty, product_id.uom_id)
        move_from_procurement = values.get('move_dest_ids')
        rerun_quantity_data = self.calculate_qty_for_rerun_move(move_from_procurement, requested_quantity)
        if bool(rerun_quantity_data):
            child_ids_from_parent = move_from_procurement.reassign_by_mo_id.procurement_group_id.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids.ids
            mrp_obj = self.env['mrp.production'].search(
                [('id', 'in', child_ids_from_parent), ('product_id', '=', product_id.id)])
            purchase_orders = mrp_obj.procurement_group_id.stock_move_ids.created_purchase_line_id.order_id | mrp_obj.procurement_group_id.stock_move_ids.move_orig_ids.purchase_line_id.order_id
            purchase_lines = purchase_orders.mapped('order_line')
            for component in mrp_obj.move_raw_ids:
                purchase_line_to_edit = purchase_lines.filtered(lambda el: el.product_id.id == component.product_id.id)
                purchase_line_to_edit.product_qty = purchase_line_to_edit.product_qty - component.product_uom_qty
            mrp_obj.action_cancel()
            self.cancelling_child_mo(mrp_obj)
            res['product_qty'] = requested_quantity
            move_from_procurement.quantity_already_processed = requested_quantity
        else:
            needed_quantity = requested_quantity - product_virtual_quantity if requested_quantity > product_virtual_quantity else 0
            if needed_quantity:
                res['product_qty'] = needed_quantity
                move_from_procurement.quantity_already_processed = needed_quantity
        return res

    # Custom or business methods
    def filter_procurements_on_forecast_qty(self, procurements):
        """
            To filter out the procurements with the forecasted quantity for buy or mto route.
        """
        procurements_to_be_considered = []
        for procurement, rule in procurements:
            product_virtual_quantity = procurement.product_id.virtual_available if procurement.product_id.virtual_available > 0 else 0
            move_from_procurement = procurement.values.get('move_dest_ids')
            requested_quantity = procurement.product_uom._compute_quantity(procurement.product_qty,
                                                                           procurement.product_id.uom_id)
            if move_from_procurement:
                quantity_already_processed_move = sum(move_from_procurement.mapped('quantity_already_processed'))
                if quantity_already_processed_move:
                    if requested_quantity > quantity_already_processed_move:
                        procurements_to_be_considered.append([procurement, rule])
                else:
                    needed_quantity = requested_quantity - product_virtual_quantity if requested_quantity > product_virtual_quantity else 0
                    if needed_quantity:
                        procurements_to_be_considered.append([procurement, rule])
                        if move_from_procurement:
                            move_from_procurement.quantity_already_processed = requested_quantity
        return procurements_to_be_considered

    def calculate_qty_for_rerun_move(self, stock_move, requested_quantity):
        """
        Preparing the dictionary for the value of the move that has already been processed.
        """
        if len(stock_move) <= 1:
            previous_quantity = stock_move.quantity_already_processed
            difference_amount = requested_quantity - previous_quantity
            rerun_data = {'difference_amount': difference_amount, 'previous_quantity': previous_quantity} if bool(
                difference_amount) else {}
            return rerun_data
        else:
            total_previous_quantity = 0
            total_requested_quantity = 0
            for move in stock_move:
                total_previous_quantity += move.quantity_already_processed
                total_requested_quantity += move.product_uom_qty
            total_difference_amount = total_previous_quantity - total_requested_quantity
            rerun_data = {'difference_amount': total_difference_amount,
                          'previous_quantity': total_previous_quantity} if bool(
                total_difference_amount) else {}
            return rerun_data

    def cancelling_child_mo(self, manufacturing_order):
        """
            This method is used for cancelling the Child MOs with recursion,
            Also removes the component quantity from Purchase order line.
        """
        for order in manufacturing_order:
            child_mo = order.procurement_group_id.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids
            if child_mo:
                self.cancelling_child_mo(child_mo)
            else:
                purchase_orders = order.procurement_group_id.stock_move_ids.created_purchase_line_id.order_id | order.procurement_group_id.stock_move_ids.move_orig_ids.purchase_line_id.order_id
                purchase_lines = purchase_orders.mapped('order_line')
                for component in order.move_raw_ids:
                    purchase_line_to_edit = purchase_lines.filtered(
                        lambda el: el.product_id.id == component.product_id.id)
                    purchase_line_to_edit.product_qty = purchase_line_to_edit.product_qty - component.product_uom_qty
                order.action_cancel()
