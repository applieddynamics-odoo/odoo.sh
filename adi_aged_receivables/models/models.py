# adi_aged_receivables/models/models.py
from odoo import models


class AgedReceivableTaxColumn(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    def _get_lines(self, options, line_id=None):
        lines = super()._get_lines(options, line_id=line_id)

        # Find our Tax column by expression_label
        tax_col_idx = None
        for i, col in enumerate(options.get("columns", [])):
            if col.get("expression_label") == "tax_total":
                tax_col_idx = i
                break
        if tax_col_idx is None:
            return lines

        Move = self.env["account.move"]

        for line in lines:
            line_ref = line.get("id")
            if not isinstance(line_ref, str):
                continue

            # Partner-grouped lines look like:
            # ~account.report~8|~account.report.line~56|groupby:partner_id~res.partner~993
            # We only want the actual partner group line (not the grand total),
            # and we will also fill the partner "total" line if present.
            if "groupby:partner_id~res.partner~" not in line_ref:
                continue

            # Extract partner_id from the line id
            try:
                partner_id = int(line_ref.split("groupby:partner_id~res.partner~")[1].split("|")[0])
            except Exception:
                continue

            # Sum tax on posted customer invoices with an outstanding balance
            # Use amount_tax_signed (company currency) so it aligns with aged receivable currency.
            moves = Move.search([
                ("partner_id", "=", partner_id),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("amount_residual", ">", 0),
            ])

            tax_total = abs(sum(moves.mapped("amount_tax_signed"))) if moves else 0.0

            if not tax_total:
                line["columns"][tax_col_idx].update({"name": "", "no_format": None})
            else:
                line["columns"][tax_col_idx].update({"no_format": tax_total})

        return lines





