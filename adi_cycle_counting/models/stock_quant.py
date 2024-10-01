from odoo import api, models, fields

# TODO: filter stock moves to ones coming from the current location!!
# TODO: filter stock moves to ones coming from the current location!!

# FIXME: A lot of magic variables in this one
inactive_mo_statuses = ["draft", "done", "cancel"]
inactive_mo_job_statuses = ["01 - Not Planned", "02 - Ready to Kit", "03 - Kitting", "done", "cancel"]

def filter_stock_moves(rec):
    moves = rec.product_id.stock_move_ids
    moves = filter(lambda i: i.raw_material_production_id, moves)
    # moves = filter(lambda m: m.location_id == rec.location_id, moves)
    moves = filter(lambda x: x.raw_material_production_id.state not in inactive_mo_statuses, moves)
    moves = filter(lambda x: x.raw_material_production_id.x_studio_job_status not in inactive_mo_job_statuses, moves)
    return moves

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # These should recaclulate every time an inventory tab is opened
    active_mo_count = fields.Integer(compute="_compute_active_mo_count", store=False)
    active_mo_list = fields.Text(compute="_compute_active_mo_list", store=False)
    qty_in_storeroom = fields.Float(compute="_compute_qty_in_storeroom", store=False, string="Quantity In Storeroom")
    qty_in_active_mos = fields.Float(compute="_compute_qty_in_active_mos", store=False, string="Quantity In Active MOs")
    
    def _compute_active_mo_count(self):
        # TODO: filter stock moves to ones coming from the current location!!
        for record in self:
            relevant_moves = filter_stock_moves(record)
            record['active_mo_count'] = len(list(relevant_moves))

    def _compute_active_mo_list(self):
        for record in self:
            record['active_mo_list'] = ""
            relevant_moves = filter_stock_moves(record)
            if relevant_moves != []:
                record['active_mo_list'] = ', '.join(set([str(move.raw_material_production_id.name or '') + ": " + str(move.raw_material_production_id.x_studio_job_status or '') for move in relevant_moves]))

    # Get the expected quantity of the item in the store room, accounting for the WIP stock 
    # which Odoo doesn't keep track of.
    # Works by querying the stock.move table for all moves, then filtering them down by the
    # raw_material_production_id variable, which is set to an MO if they are used in it
    # the amount can be queried from the move
    # Matt Younger 2023-08-31
    def _compute_qty_in_storeroom(self):        
        for record in self:
            record['qty_in_storeroom'] = record.quantity
            if filter_virtual_location(record):
                moves = filter_stock_moves(record)
                amt = sum([move.product_uom_qty for move in moves]) # sum qty in current orders
                record['qty_in_storeroom'] = record.quantity - amt # adjust the inventory by that amount

    @api.depends("qty_in_storeroom")
    def _compute_qty_in_active_mos(self):
        for record in self:
            record['qty_in_active_mos'] = record.quantity - record.qty_in_storeroom
    
def filter_virtual_location(quant):
    loc = quant.location_id
    while loc.location_id:
        loc = loc.location_id
    return loc.name not in ["Virtual Locations", "Partner Locations"]

def filter_job_status(move):
  return move.raw_material_production_id.x_studio_job_status not in ["01 - Not Planned", "02 - Ready to Kit", "03 - Kitting", "done", "cancel"]
