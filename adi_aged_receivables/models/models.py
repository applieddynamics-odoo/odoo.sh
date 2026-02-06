# adi_aged_receivables/models/models.py
import re
from odoo import models


class AgedReceivableTaxColumn(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    def _custom_line_postprocessor(self, report, options, lines, warnings=None, **kwargs):
        lines = super()._custom_line_postprocessor(report, options, lines, warnings=warnings, **kwargs)

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

        # Cache: partner total tax and per-move tax
        tax_by_commercial_partner = {}
        move_tax_by_name = {}

        def _set_tax(line_dict, value):
            if tax_col_idx >= len(line_dict.get("columns", [])):
                return

            col = line_dict["columns"][tax_col_idx]

            if not value:
                col.update({"name": "", "no_format": 0.0, "is_zero": True})
                return

            val = float(value)
            formatted = report.format_value(
                options,
                val,
                figure_type=col.get("figure_type") or "monetary",
                currency=col.get("currency"),
                digits=col.get("digits"),
            )
            col.update({"no_format": val, "name": formatted, "is_zero": False})

        def _extract_move_name(line_name):
            """
            Invoice lines show something like:
              '200/2026/0005 (8000000467)'
            Return '200/2026/0005'
            """
            if not line_name or not isinstance(line_name, str):
                return None
            m = re.match(r"^\s*([A-Za-z0-9]+\/\d{4}\/\d+)", line_name)
            return m.group(1) if m else None

        company_id = self.env.company.id

        for line in lines:
            line_id = line.get("id")
            if not isinstance(line_id, str):
                continue

            # 1) Invoice rows: detect by parsing the displayed invoice number in the line name
            move_name = _extract_move_name(line.get("name"))
            if move_name:
                cache_key = (company_id, move_name)
                if cache_key not in move_tax_by_name:
                    move = Move.search([
                        ("company_id", "=", company_id),
                        ("name", "=", move_name),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                    ], limit=1)
                    move_tax_by_name[cache_key] = abs(move.amount_tax_signed or 0.0) if move else 0.0

                _set_tax(line, move_tax_by_name[cache_key])
                continue

            # 2) Partner grouped lines: only apply to the partner header/total lines
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
                        ("company_id", "=", company_id),
                        ("commercial_partner_id", "=", commercial.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                        ("amount_residual", ">", 0),
                    ])
                    tax_by_commercial_partner[commercial.id] = abs(sum(moves.mapped("amount_tax_signed"))) if moves else 0.0

                _set_tax(line, tax_by_commercial_partner[commercial.id])

        return lines











