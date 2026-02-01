# -*- coding: utf-8 -*-

from odoo import models, fields, api

'''
class adi_aged_receivables(models.Model):
    _name = "adi.aged.receivables"
    _table = "adi_aged_receivables_adi_aged_receivables"
    _inherit = "account.aged.receivable"
    _description = "Aged Receivable ADI"
    _auto = False

    invoice_date = fields.Date(_compute="_compute_invoice_date")

    def _compute_invoice_date(self):
        for r in self:
            r.journal_id.invoice_date

    @api.model
    def _get_report_name(self):
        return _("ADI Aged Receivable")
''''''
    @api.model
    def _get_templates(self):
        # OVERRIDE
        templates = super(ReportAccountAgedReceivable, self)._get_templates()
        templates['line_template'] = 'adi_aged_receivables.line_template_aged_receivable_report'
        return templates
'''
