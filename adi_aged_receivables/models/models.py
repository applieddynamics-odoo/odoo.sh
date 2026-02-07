# adi_aged_receivables/models/models.py
import re
from odoo import models


class AgedReceivableTaxAndDescription(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    def _custom_line_postprocessor(self, report, options, lines, warnings=None, **kwargs):
        lines = super()._custom_line_postprocessor(report, options, lines, warnings=warnings, **kwargs)

        # Locate Tax + Description columns by expression_label
        tax_col_idx = None
        desc_col_idx = None
        for i, col in enumerate(options.get("columns", [])):
            label = col.get("expression_label")
            if label == "tax_total":
                tax_col_idx = i
            elif label == "description":
                desc_col_idx = i

        # If neither column exists, nothing to do
        if tax_col_idx is None and desc_col_idx is None:
            return lines

        Partner = self.env["res.partner"]
        Move = self.env["account.move"]
        company_id = self.env.company.id

        # Caches
        tax_by_commercial_partner = {}          # commercial_partner_id -> tax_total
        move_cache_by_name = {}                # (company_id, move_name) -> (tax, description)

        def _set_tax(line_dict, value):
            if tax_col_idx is None or tax_col_idx >= len(line_dict.get("columns", [])):
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

        def _set_text(line_dict, value):
            if desc_col_idx is None or desc_col_idx >= len(line_dict.get("columns", [])):
                return
            col = line_dict["columns"][desc_col_idx]
            txt = (value or "").strip() if isinstance(value, str) else (value or "")
            col.update({
                "name": txt,
                "no_format": txt,
                "is_zero": not bool(txt),
            })

        def _extract_move_name(line_name):
            """
            Invoice line names look like:
              '200/2026/0005 (8000000467)'
            Return:
              '200/2026/0005'
            """
            if not line_name or not isinstance(line_name, str):
                return None
            m = re.match(r"^\s*([A-Za-z0-9]+\/\d{4}\/\d+)", line_name)
            return m.group(1) if m else None

        for line in lines:
            line_id = line.get("id")
            if not isinstance(line_id, str):
                continue

            # ------------------------------------------------------------
            # 1) Invoice rows: derive account.move from the displayed name
            # ------------------------------------------------------------
            move_name = _extract_move_name(line.get("name"))
            if move_name:
                cache_key = (company_id, move_name)
                if cache_key not in move_cache_by_name:
                    move = Move.search([
                        ("company_id", "=", company_id),
                        ("name", "=", move_name),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                    ], limit=1)
                    tax_val = abs(move.amount_tax_signed or 0.0) if move else 0.0
                    desc_val = move.x_studio_inv_milestone_name if move else ""
                    move_cache_by_name[cache_key] = (tax_val, desc_val)

                tax_val, desc_val = move_cache_by_name[cache_key]
                _set_tax(line, tax_val)
                _set_text(line, desc_val)
                continue

            # ------------------------------------------------------------
            # 2) Partner grouped lines: set partner Tax total only
            #    (Description stays blank on totals/headers as requested)
            # ------------------------------------------------------------
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

                # Force Description blank on partner/total lines
                _set_text(line, "")
                continue

        return lines












