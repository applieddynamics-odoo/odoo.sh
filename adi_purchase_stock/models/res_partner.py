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
        for record in self:
            self._cr.execute(
                """
                SELECT COUNT(pl.id) FROM purchase_order_line pl
                    JOIN purchase_order   po ON pl.order_id = po.id
                    JOIN product_product   p ON pl.product_id = p.id
                    JOIN product_template pt ON p.product_tmpl_id = pt.id
                    JOIN product_category pc ON pt.categ_id = pc.id
                WHERE pl.partner_id = %d AND po.date_order::date >= '%s'::date AND
                      pt.detailed_type != 'service' AND
                      pc.name != 'Office Supplies' AND
                      pc.name != 'Production Supplies';
                """ %
                (record.id, (datetime.now() - timedelta(365)).strftime("%Y-%m-%d"))
            )
            order_lines_cnt = self._cr.fetchone()[0]
            self._cr.execute(
                """
                SELECT COUNT(pl.id) FROM purchase_order_line pl
                    JOIN purchase_order   po ON pl.order_id = po.id
                    JOIN product_product   p ON pl.product_id = p.id
                    JOIN product_template pt ON p.product_tmpl_id = pt.id
                    JOIN product_category pc ON pt.categ_id = pc.id
                WHERE pl.partner_id = %d AND po.date_order::date >= '%s'::date AND
                      pt.detailed_type != 'service' AND
                      pc.name != 'Office Supplies' AND
                      pc.name != 'Production Supplies' AND
                      (SELECT BOOL_OR(sp.date_done > sp.scheduled_date)
                           FROM stock_move m JOIN stock_picking sp
                           ON m.picking_id = sp.id
                       WHERE m.purchase_line_id = pl.id AND m.state = 'done') = true;
                """ %
                (record.id, (datetime.now() - timedelta(365)).strftime("%Y-%m-%d"))
            )
            on_time_cnt = order_lines_cnt - self._cr.fetchone()[0]
            record['on_time_rate'] = on_time_cnt / order_lines_cnt * 100
            # record['on_time_rate'] = len(moves)/len(order_lines) * 100
            '''
            order_lines = self.env['purchase.order.line'].search([
                ('partner_id', '=', self.id),
                ('date_order', '>', fields.Date.today() - timedelta(365)),
                ('order_id.state', 'in', ['done', 'purchase']),
                ('product_id.product_tmpl_id.type', '!=', 'service'),
                ('product_id.product_tmpl_id.type', '!=', 'consumable'),
                ('product_id.x_studio_product_classification', '!=', ''),
                ('product_id.categ_id.name', '!=', 'Office Supplies'),
                ('product_id.categ_id.name', '!=', 'Production Supplies'),
            ])
            if len(order_lines) == 0:
                record['on_time_rate'] = -1
                continue
            moves = self.env['stock.move'].search([
                ('purchase_line_id', 'in', order_lines.ids),
                ('state', '=', 'done'),
            ]).filtered(lambda m: m.date.date() <= m.purchase_line_id.date_planned.date())

            # reduce the moves so that there is at most 1 per purchase order line
            # this doesn't accurately capture the total number received vs
            # expected so is not a full solution...
            moves = set(moves.mapped("purchase_line_id"))
            """
            line_qty_totals = {l.id : l.product_qty for l in order_lines}
            move_totals = defaultdict(lambda: 0)
            for m in moves:
                move_totals[m.purchase_line_id] += m.quantity_done
            total_finished = sum([0 if move_totals[i] < line_qty_totals[i] else 1 for i in line_qty_totals.keys()])
            """
            '''
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
