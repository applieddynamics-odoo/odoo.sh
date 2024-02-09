# -*- coding: utf-8 -*-

from odoo import models, fields, api
from collections import defaultdict

import datetime

def merge_bom_dicts(a, b):
    c = a
    for l in b.items():
        if c.get(l[0]):
            c[l[0]]['qty'] += l[1]['qty']
        else:
            c[l[0]] = l[1]
    return c

def get_bom_lines_dict(bom, top_bom, depth=0):
    res = dict()
    for line in bom.bom_line_ids:
        if line.child_bom_id:
            tmp = get_bom_lines_dict(line.child_bom_id, bom, depth+1)
            res = merge_bom_dicts(res, tmp)
        if res.get(line.product_id):
            res[line.product_id]['qty'] += line.product_qty
        else:
            res[line.product_id] = {
                'product': line.product_id,
                'qty': line.product_qty,
                'depth': -1,
                'bom': top_bom
            }
    return res

def get_bom_lines_list(bom, top_bom, depth=0):
    res = []
    for line in bom.bom_line_ids:
        if line.child_bom_id:
            res += get_bom_lines_list(line.child_bom_id, top_bom, depth+1)
        res.append({
            'product': line.product_id,
            'qty': line.product_qty,
            'depth': depth,
            'bom': top_bom
        })
    return res

get_bom_lines = get_bom_lines_dict

def get_last_purchased(env, p):
    #lines = env['purchase.order.line'].search([('product_id', '=', p.id), ('order_id.date_approve', '!=', None), ('order_id.state', '!=', 'cancel')], order="date_order desc")
    lines = p.purchase_order_line_ids.filtered(lambda p: p.order_id.date_approve and p.order_id.state != 'cancel')
    if len(lines) == 0:
        return None
    lines = [l.order_id.date_approve for l in lines]
    return sorted(lines, reverse=True)[0]

class flattened_bom(models.Model):
    _name = "flattened_bom.flattened_bom"
    _description = "Flattened View of a BOM"

    last_time_purchased = fields.Date(string="Last Purchase Date")
    bom_depth = fields.Integer()
    order_id = fields.Many2one('sale.order')
    partner_id = fields.Many2one('res.partner')
    sale_order = fields.Many2one('sale.order')
    bom_id = fields.Many2one('mrp.bom')
    part_number = fields.Char()
    product_name = fields.Char()
    product = fields.Many2one('product.product')
    exclude_from_maintenance = fields.Char()
    quantity = fields.Float()
    product_category = fields.Many2one('product.category')
    product_classification = fields.Char()
    us_eccn = fields.Char()
    manufacturer = fields.Many2one('res.partner')
    manufacturer_pn = fields.Char()
    lifecycle_status = fields.Char()
    computed_lifecycle_status = fields.Char(compute="_compute_lifecycle_status")
    origin_country = fields.Many2one('res.country')
    rma_count = fields.Integer(compute="_compute_rmas", store=True)
    last_purchased = fields.Date(compute="_get_last_purchased")
    last_purchased_po = fields.Many2one('purchase.order', store=False)
    last_purchased_price = fields.Float(store=False)

    def _get_last_purchased(self):
        for r in self:
            p = r.product.product_variant_ids[0]
            lines = p.purchase_order_line_ids.filtered(lambda p: p.order_id.date_approve and p.order_id.state != 'cancel')
            if len(lines) == 0:
                r['last_purchased'] = None
                continue
            line_dates = [l.order_id.date_approve for l in lines]
            last_purchased = sorted(line_dates, reverse=True)[0]
            r['last_purchased'] = last_purchased
            r['last_purchased_po'] = [l for l in lines if l.order_id.date_approve == last_purchased][0].order_id
            r['last_purchased_price'] = [l for l in lines if l.order_id.date_approve == last_purchased][0].price_unit
    
    @api.depends('product')
    def _compute_lifecycle_status(self):
        # exclude documents from flowing up
        # treat unknown as active
        # ignore mature + eol for now
        values = {
            'Product Lifestyle Status': 2,
            'Obsolete': 1,
            'Legacy': 0,
            'End of Life': 3,
            'Mature': 4,
            'Active': 5
        }
        for r in self:
            if len(r.product.product_tmpl_id.bom_ids) == 0:
                r['computed_lifecycle_status'] = "Unknown"
                continue
            bom = r.product.product_tmpl_id.bom_ids[0]
            items = get_bom_lines(bom, bom)
            val = 5
            for i in items.values():
                val = min(val, values[i['product'].x_studio_product_lifecycle_status])
            r['computed_lifecycle_status'] = str([k for k, v in values.items() if v == val][0])
    
    @api.depends('product')
    def _compute_rmas(self):
        for r in self:
            r['rma_count'] = len(self.env['repair.order'].search([('product_id', '=', r.product.id)]))

    @api.model
    def create(self, values):
        if not values.get('product'):
            self.search([]).unlink()
            items = None
            if values.get('bom_id'):
                items = self.load_bom(values['bom_id'])
            elif values.get('order_id'):
                items = self.load_order_boms(values['order_id'])
            else:
                items = self.load_customer_boms(values['partner_id'])
            self.add_items(items)
            self.env.cr.commit()
            override_create = super(flattened_bom, self).create(values)
            return override_create

        override_create = super(flattened_bom, self).create(values)
        return override_create

    def add_items(self, items):
        for line in items.values():
            p = line['product']
            self.create({
                'bom_id': line['bom'].id,
                'bom_depth': line['depth'],
                'part_number': p.default_code, 
                'product': p.id,
                'product_name': p.name,
                'quantity': line['qty'],
                'product_category': p.categ_id.id,
                'us_eccn': p.x_studio_us_eccn,
                'manufacturer': p.x_studio_manufacturer.id,
                'manufacturer_pn': p.x_studio_manufacturer_pn,
                'lifecycle_status': p.x_studio_product_lifecycle_status,
                'origin_country': p.x_studio_product_country_of_origin.id,
                'last_time_purchased': get_last_purchased(self.env, p),
                'product_classification': p.x_studio_product_classification,
                'exclude_from_maintenance': p.x_studio_maintenance_excluded
            })
    
    def load_bom(self, bom_id):
        bom = self.env['mrp.bom'].search([('id', '=', bom_id)])[0]
        return get_bom_lines(bom, bom)

    def load_order_boms(self, order_id):
        lines = dict()
        sale = self.env['sale.order'].search([('id', '=', order_id)])[0]
        for line in sale.order_line:
            if not line.product_id:
                continue
            boms = line.product_id.product_tmpl_id.bom_ids
            if len(boms) == 0:
                continue
            if len(boms) > 1:
                raise Exception("There are duplicate boms for product: " + (line.product_id.default_code or ""))
            lines = merge_bom_dicts(lines, get_bom_lines(boms[0], boms[0]))

        for k in lines.keys():
            lines[k]['order_id'] = order_id
        return lines

    def load_customer_boms(self, customer):
        lines = dict()
        sales = self.env['sale.order'].search([('partner_id', '=', customer)])
        for sale in sales:
            lines = merge_bom_dicts(lines, self.load_order_boms(sale.id))
        
        return lines
