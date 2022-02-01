# -*- coding: utf-8 -*-

from odoo import models, fields


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        moves_todo = super()._action_done(cancel_backorder=cancel_backorder)
        picking = moves_todo.mapped('picking_id')
        picking = picking.browse(self.env.context.get('button_validate_picking_ids')) if not picking else picking
        if picking:
            moves_todo.write({'date': picking.date_done})
        return moves_todo

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            purchase_order =  self.purchase_line_id.order_id if self.purchase_line_id else False
            ctx = self.env.context
            if purchase_order:
                date = ctx.get('force_period_date', self.picking_id.date_done)
            else:
                date = ctx.get('force_period_date', fields.Date.context_today(self))

            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
            })
            new_account_move._post()
