import pytz
from datetime import timedelta, datetime
from collections import defaultdict
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_view_order_lines(self):
        act = self.env.ref('adi_purchase_stock.purchase_order_line_new_tree_adi').read()[0]
        act['domain'] =
        [
            ('partner_id', '=', self.id),
            ('date_order', '>', datetime.now() - timedelta(365)),
            ('product_id.product_tmpl_id.categ_id.name', '!=', 'Office Supplies'),
            ('product_id.product_tmpl_id.categ_id.name', '!=', 'Production Supplies'),
            ('product_id.product_tmpl_id.detailed_type', '!=', 'service')
        ]
        return act

    @api.depends('purchase_line_ids')
    def _compute_on_time_rate(self):
        for record in self:
            self._cr.execute(
                """SELECT COALESCE(AVG(1.0 - pol.arrived_late::int), -0.01)
                FROM purchase_order_line pol JOIN purchase_order po
                    ON pol.order_id = po.id
                JOIN product_product p ON pol.product_id = p.id
                JOIN product_template pt ON p.product_tmpl_id = pt.id
                JOIN product_category pc ON pt.categ_id = pc.id
                WHERE pol.partner_id = %d AND po.date_order::date >= '%s'::date
                    AND pt.detailed_type != 'service'
                    AND pc.name != 'Office Supplies'
                    AND pc.name != 'Production Supplies';"""
                % (record.id, (datetime.now() - timedelta(365)).strftime("%Y-%m-%d")))
            avg = self._cr.fetchone()[0]
            record['on_time_rate'] = avg * 100
