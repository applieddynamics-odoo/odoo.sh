from odoo import api, models, fields

class RepairOrder(models.Model):
    _inherit="repair.order"

    state = fields.Selection([("draft", "New"), ("confirmed", "Received"), ("under_repair", "Under Repair"), ("done", "Repaired"), ("cancel", "Cancelled")])
