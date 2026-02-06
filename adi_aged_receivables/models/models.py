# adi_aged_receivables/models/models.py
from odoo import models


class AgedReceivableTaxColumn(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    def _custom_line_postprocessor(self, report, options, lines, warnings=None, **kwargs):
        # Always call super first (pass through warnings/kwargs)
        lines = super()._custom_line_postprocessor(report, options, lines, warnings=warnings, **kwargs)

        # Find Tax column position by expression_label (must be 'tax_total' in the report column)
        tax_col_idx = None
        for i, col in enumerate(options.get("columns", [])):
            if col.get("expression_label") == "tax_total":
                tax_col_idx = i
                break
        if tax_col_idx is None:
            return lines

        Partner = self.env["res.partner"]
        Move = self.env["account.move"]

        # Cache totals per commercial partner to avoid repeated searches
        tax_by_commercial_partner = {}

        def _set_tax(line_dict, value):
            """Write tax value into the Tax column; show blank when zero."""
            if tax_col_idx >= len(line_dict.get("columns", [])):
                return

            col = line_dict["columns"][tax_col_idx]

            if not value:
                col.update({
                    "name": "",
                    "no_format": 0.0,
                    "is_zero": True,
                })
                return

            val = float(value)

            # IMPORTANT: In your build, format_value signature is (options, value, ...)
            formatted = report.format_value(
                options,
                val,
                figure_type=col.get("figure_type") or "monetary",
                currency=col.get("currency"),
                digits=col.get("digits"),
            )

            col.update({
                "no_format": val,
                "name": formatted,
                "is_zero": False,
            })

        for line in lines:
            line_id = line.get("id")
            if not isinstance(line_id, str):
                continue

            # Partner-grouped line ids like:
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

            # Optional: invoice/unfold lines sometimes contain an account.move id
            if "~account.move~" in line_id:
                try:
                    move_id = int(line_id.split("~account.move~")[1].split("|")[0].split("~")[0])
                except Exception:
                    continue

                move = Move.browse(move_id)
                if move.exists():
                    _set_tax(line, abs(move.amount_tax_signed or 0.0))

        return lines










