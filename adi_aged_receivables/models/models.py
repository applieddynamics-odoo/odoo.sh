# -*- coding: utf-8 -*-

from odoo import models


class ReportAccountAgedReceivableADI(models.AbstractModel):
    _inherit = "account.aged.receivable"

    def _get_templates(self):
        templates = super()._get_templates()
        templates["line_template"] = "adi_aged_receivables.line_template_aged_receivable_report"
        return templates

