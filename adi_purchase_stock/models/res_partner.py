import pytz
from datetime import timedelta
from collections import defaultdict
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def should_warn(self):
        for partner in self:
            if 0 <= partner.on_time_rate <= self.env.company.on_time_threshold:
                return True
        return False

    @api.depends('purchase_line_ids')
    def _compute_on_time_rate(self):
        for record in self:
             self._cr.execute("SELECT AVG(1 - pol.arrived_late::int) FROM purchase_order_line as pol JOIN purchase_order as po ON pol.order_id = po.id WHERE pol.partner_id = %d AND po.date_order::date >= '%s'::date;" % (record.id, datetime.now().strftime("%Y-%m-%d")))
            avg = self._cr.fetchone()[0]
            record['on_time_rate'] = avg * 100
