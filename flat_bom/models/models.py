# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

def get_all_nested_line_ids(bom):
    res = []
    for line in bom.bom_line_ids:
        if line.child_bom_id:
            res += get_all_nested_line_ids(line.child_bom_id)
        res.append(line)
    return res

class flat_bom(models.Model):
    _name = 'flat_bom.flat_bom'
    _description = 'Flattened BOM and the sale order it appears on'

    name = fields.Char()
    bom_id = fields.Many2one('mrp.bom')
    sale_order_id = fields.Many2one('sale.order')

    def create_flat_boms(self):
        self.search([]).unlink()
        self.env['flat_bom.flat_bom_relation'].search([]).unlink()
        for so in self.env['sale.order'].search([]):
            for line in so.order_line:
                boms = self.env['mrp.bom'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])
                if len(boms) > 0:
                    self.create_flat_bom(boms[0], so)
        self.env.cr.commit()
        
    
    def create_flat_bom(self, bom, so):
        flat_bom_id = self.create({
            'name': bom.code,
            'bom_id': bom.id,
            'sale_order_id': so.id
        })
        
        for line in get_all_nested_line_ids(bom):
            self.env['flat_bom.flat_bom_relation'].create({
                'flat_bom_id': flat_bom_id.id,
                'bom_line_id': line.id,
            })
        pass
        

class flat_bom_relation(models.Model):
    _name = 'flat_bom.flat_bom_relation'
    _description = 'Relationship model from flat bom to bom line ids'

    flat_bom_id = fields.Many2one('flat_bom.flat_bom')
    bom_line_id = fields.Many2one('mrp.bom.line')

class flat_bom_view(models.Model):
    _name = 'flat_bom.flat_bom.view'
    _description = 'PSQL View for flat bom'
    _auto = False
    _rec_name = 'part_number'

    last_purchased = fields.Date(string="Last Purchase Date", compute="_get_last_purchased")
    sale_order_id = fields.Many2one('sale.order')
    partner_id = fields.Many2one('res.partner')

    product_id  = fields.Many2one('product.template')
    part_number = fields.Char("Part Number")
    product_category_id = fields.Many2one('product.category')
    product_exclude_from_maintenance = fields.Char()
    product_classification = fields.Char()
    product_name = fields.Char("Product Name")
    product_us_eccn = fields.Char("US ECCN")
    lifecycle_status = fields.Char("Lifecycle Status")
    manufacturer_id = fields.Many2one('res.partner')
    manufacturer_pn = fields.Char()
    
    flat_bom_id = fields.Many2one('flat_bom.flat_bom')
    quantity = fields.Float()
    last_purchased = fields.Date(string="Last Purchase Date", compute="_get_last_purchased")
    last_purchased_po = fields.Many2one('purchase.order', store=False)
    last_purchased_price = fields.Float(store=False)

    def _get_last_purchased(self):
        for r in self:
            p = r.product_id.product_variant_ids[0]
            lines = p.purchase_order_line_ids.filtered(lambda p: p.order_id.date_approve and p.order_id.state != 'cancel')
            if len(lines) == 0:
                r['last_purchased'] = None
                continue
            line_dates = [l.order_id.date_approve for l in lines]
            last_purchased = sorted(line_dates, reverse=True)[0]
            r['last_purchased'] = last_purchased
            r['last_purchased_po'] = [l for l in lines if l.order_id.date_approve == last_purchased][0].order_id
            r['last_purchased_price'] = [l for l in lines if l.order_id.date_approve == last_purchased][0].price_unit
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'flat_bom_flat_bom_view')
        self._cr.execute("""CREATE OR REPLACE VIEW flat_bom_flat_bom_view AS (
            SELECT
                fbr.id as id,
                p.id as product_id,
                p.default_code as part_number,
                p.name as product_name,
                p.x_studio_us_eccn as product_us_eccn,
                p.x_studio_manufacturer as manufacturer_id,
                p.x_studio_manufacturer_pn as manufacturer_pn,
                p.x_studio_product_lifecycle_status as lifecycle_status,
                p.categ_id as product_category_id,
                p.x_studio_product_classification as product_classification,
                p.x_studio_maintenance_excluded as product_exclude_from_maintenance,
                
                mbl.product_qty as quantity,
                
                fb.id as flat_bom_id,
                s.id as sale_order_id,
                s.partner_id as partner_id
            FROM
                flat_bom_flat_bom_relation as fbr
            INNER JOIN
                flat_bom_flat_bom as fb ON fb.id = fbr.flat_bom_id
            INNER JOIN
                mrp_bom_line as mbl ON mbl.id = fbr.bom_line_id
            INNER JOIN
                product_template as p ON p.id = mbl.product_tmpl_id
            INNER JOIN
                sale_order as s on s.id = fb.sale_order_id
        )""")
