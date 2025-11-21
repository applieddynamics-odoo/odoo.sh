from odoo import api, models, fields

class RepairOrder(models.Model):
    _inherit="repair.order"

    state = fields.Selection([("draft", "Draft"), ("confirmed", "Received"), ("under_repair", "In Progress"), ("done", "Complete"), ("cancel", "Cancelled")])
