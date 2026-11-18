from odoo import models, fields


class StockMove(models.Model):
    _inherit = "stock.move"

    # Retained for compatibility with existing database records.
    quantity_already_processed = fields.Float(
        string="Quantity already processed"
    )

    reassign_by_mo_id = fields.Many2one(
        "mrp.production",
        string="Reassign by MO"
    )