# -*- coding: utf-8 -*-

import pytz
from datetime import timedelta, datetime
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
        order_lines = self.env['purchase.order.line'].search([
            ('partner_id', 'in', self.ids),
            ('date_order', '>', fields.Date.today() - timedelta(365)),
            ('qty_received', '!=', 0),
            ('order_id.state', 'in', ['done', 'purchase'])
        ]).filtered(lambda l: l.product_id.sudo().product_tmpl_id.type != 'service')
        lines_qty_done = defaultdict(lambda: 0)
        local_time = pytz.timezone(self.env.context.get('tz', 'utc') or 'utc')
        ctx = self.env.context
        tzInfo = pytz.timezone(ctx.get('tz'))
        moves = self.env['stock.move'].search([
            ('purchase_line_id', 'in', order_lines.ids),
            # custom code started
            ('state', '=', 'done')]).filtered(lambda m: m.date.astimezone(tz=tzInfo).date() <= m.purchase_line_id.date_planned.astimezone(tz=tzInfo).date())
            # client want with time as well

        for move, qty_done in zip(moves, moves.mapped('quantity_done')):
            lines_qty_done[move.purchase_line_id.id] += qty_done
        partner_dict = {}
        for line in order_lines:
            on_time, ordered = partner_dict.get(line.partner_id, (0, 0))
            ordered += line.product_uom_qty
            on_time += lines_qty_done[line.id]
            partner_dict[line.partner_id] = (on_time, ordered)
        seen_partner = self.env['res.partner']
        for partner, numbers in partner_dict.items():
            seen_partner |= partner
            on_time, ordered = numbers
            partner.on_time_rate = on_time / ordered * 100 if ordered else -1   # use negative number to indicate no data
        (self - seen_partner).on_time_rate = -1
