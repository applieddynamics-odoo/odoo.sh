from odoo import models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Custom methods
    def action_run_moves(self):
        """
        Method to call on the button Run Moves
        """
        new_procurement_requests = []
        for move in self.move_raw_ids:
            move.reassign_by_mo_id = self.id
            if move.quantity_already_processed:
                values = move._prepare_procurement_values()
                origin = (move.group_id and move.group_id.name or (move.origin or move.picking_id.name or "/"))
                new_procurement_requests.append(self.env['procurement.group'].Procurement(
                    move.product_id, move.product_uom_qty, move.product_uom,
                    move.location_id, move.rule_id and move.rule_id.name or "/",
                    origin, move.company_id, values))
        self.env['procurement.group'].run(new_procurement_requests,
                                          raise_user_error=not self.env.context.get('from_orderpoint'))
