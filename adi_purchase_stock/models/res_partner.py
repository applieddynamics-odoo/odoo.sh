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
            self._cr.execute("""SELECT SUM(pol.arrived_late::int), COUNT(pol.id) FROM purchase_order_line as pol WHERE pol.partner_id = """ + str(record.id) + ";")
            raise Exception(self._cr.fetchall())
            record['on_time_rate'] = -1
