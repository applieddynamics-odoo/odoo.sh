# adi_aged_receivables/models/models.py
from odoo import models


class AgedReceivableTaxColumn(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    def _get_lines(self, options, line_id=None):
        lines = super()._get_lines(options, line_id=line_id)

        # Find the Tax column (created in the report with expression_label = 'tax_total')
        tax_col_idx = None
        for i, col in enumerate(options.get("columns", [])):
            if col.get("expression_label") == "tax_total":
                tax_col_idx = i
                break
        if tax_col_idx is None:
            return lines

        Partner = self.env["res.partner"]
        Move = self.env["account.move"]

        for line in lines:
            line_ref = line.get("id")
            if not isinstance(line_ref, str):
                continue

            # Example:
            # ~account.report~8|~account.report.line~56|groupby:partner_id~res.partner~993
            if "groupby:partner_id~res.partner~" not in line_ref:
                continue

            try:
                partner_id = int(line_ref.split("groupby:partner_id~res.partner~")[1].split("|")[0])
            except Exception:
                continue

            partner = Partner.browse(partner_id)
            if not partner.exists():
                continue

            commercial = partner.commercial_partner_id

            # Aged receivable is in company currency -> use amount_tax_signed (company currency)
            moves = Move.search([
                ("commercial_partner_id", "=", commercial.id),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("amount_residual", ">", 0),
            ])

            tax_total = abs(sum(moves.mapped("amount_tax_signed"))) if moves else 0.0

            # Blank when zero
            if not tax_total:
                line["columns"][tax_col_idx].update({"name": "", "no_format": None})
            else:
                line["columns"][tax_col_idx].update({"no_format": tax_total})

        return lines






