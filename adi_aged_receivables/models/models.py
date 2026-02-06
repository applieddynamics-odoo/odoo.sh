# adi_aged_receivables/models/models.py
from odoo import models


class AgedReceivableTaxColumn(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    def _custom_line_postprocessor(self, report, options, lines):
        # Always call super first
        lines = super()._custom_line_postprocessor(report, options, lines)

        # Find Tax column position by expression_label
        tax_col_idx = None
        for i, col in enumerate(options.get("columns", [])):
            if col.get("expression_label") == "tax_total":
                tax_col_idx = i
                break
        if tax_col_idx is None:
            return lines

        Partner = self.env["res.partner"]
        Move = self.env["account.move"]

        # Cache tax totals per commercial partner for speed
        tax_by_commercial_partner = {}

        def _set_tax(line_dict, value):
            """Write numeric value (company currency) into the tax column; blank if 0."""
            if tax_col_idx >= len(line_dict.get("columns", [])):
                return
            if not value:
                line_dict["columns"][tax_col_idx].update({"name": "", "no_format": None})
            else:
                line_dict["columns"][tax_col_idx].update({"no_format": float(value)})

        for line in lines:
            line_id = line.get("id")
            if not isinstance(line_id, str):
                continue

            # Case A: Partner-grouped line ids like:
            # ~account.report~8|~account.report.line~56|groupby:partner_id~res.partner~993
            if "groupby:partner_id~res.partner~" in line_id:
                try:
                    partner_id = int(line_id.split("groupby:partner_id~res.partner~")[1].split("|")[0])
                except Exception:
                    continue

                partner = Partner.browse(partner_id)
                if not partner.exists():
                    continue

                commercial = partner.commercial_partner_id

                if commercial.id not in tax_by_commercial_partner:
                    moves = Move.search([
                        ("commercial_partner_id", "=", commercial.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                        ("amount_residual", ">", 0),
                    ])
                    tax_by_commercial_partner[commercial.id] = abs(sum(moves.mapped("amount_tax_signed"))) if moves else 0.0

                _set_tax(line, tax_by_commercial_partner[commercial.id])
                continue

            # Case B (optional): Unfolded invoice lines sometimes contain an account.move id.
            # Common patterns include "...~account.move~123" inside the line id.
            if "~account.move~" in line_id:
                try:
                    move_id = int(line_id.split("~account.move~")[1].split("|")[0].split("~")[0])
                except Exception:
                    continue

                move = Move.browse(move_id)
                if not move.exists():
                    continue

                _set_tax(line, abs(move.amount_tax_signed or 0.0))
                continue

        return lines







