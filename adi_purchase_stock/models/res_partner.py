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
            order_lines = self.env['purchase.order.line'].search([
                ('partner_id', '=', self.id),
                ('date_order', '>', fields.Date.today() - timedelta(365)),
                ('order_id.state', 'in', ['done', 'purchase']),
                ('product_id.product_tmpl_id.type', '!=', 'service'),
                ('product_id.product_tmpl_id.type', '!=', 'consumable'),
                ('product_id.x_studio_product_classification', '!=', ''),
            ])
            if len(order_lines) == 0:
                record['on_time_rate'] = -1
                continue
            move_ids = self.env['stock.move'].search([
                ('purchase_line_id', 'in', order_lines.ids),
            ])
            raise Exception(move_ids)
        '''
        order_lines = self.env['purchase.order.line'].search([
            ('partner_id', 'in', self.ids),
            ('date_order', '>', fields.Date.today() - timedelta(365)),
            ('qty_received', '!=', 0),
            ('order_id.state', 'in', ['done', 'purchase'])
        ]).filtered(lambda l: l.product_id.sudo().product_tmpl_id.type != 'service')
        lines_qty_done = defaultdict(lambda: 0)
        tzInfo = pytz.timezone(self.env.context.get('tz')) if self.env.context.get('tz') else pytz.timezone('utc')
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
            partner_dict[line.partner_id] = (on_time + lines_qty_done[line.id], ordered + line.product_uom_qty)
        seen_partner = self.env['res.partner']
        for partner, numbers in partner_dict.items():
            seen_partner |= partner
            on_time, ordered = numbers
            partner.on_time_rate = on_time / ordered * 100 if ordered else -1   # use negative number to indicate no data
        (self - seen_partner).on_time_rate = -1
        '''
