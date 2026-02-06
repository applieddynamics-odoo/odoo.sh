from odoo import models


class AgedReceivableTaxColumn(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    def _get_lines(self, options, line_id=None):
        lines = super()._get_lines(options, line_id=line_id)

        # Only act if the report includes our column
        tax_col_idx = None
        for i, col in enumerate(options.get("columns", [])):
            if col.get("expression_label") == "tax_total":
                tax_col_idx = i
                break
        if tax_col_idx is None:
            return lines

        MoveLine = self.env["account.move.line"]

        for line in lines:
            line_ref = line.get("id")

            # Only journal item lines look like "account.move.line,123"
            if not (isinstance(line_ref, str) and line_ref.startswith("account.move.line,")):
                continue

            try:
                aml_id = int(line_ref.split(",")[1])
            except Exception:
                continue

            aml = MoveLine.browse(aml_id)
            if not aml.exists():
                continue

            move = aml.move_id

            # Sum of tax journal lines on the move (company currency)
            tax_lines = move.line_ids.filtered(lambda l: l.tax_line_id)
            tax_total = abs(sum(tax_lines.mapped("balance")))

            # Blank cell if 0
            if not tax_total:
                line["columns"][tax_col_idx].update({"name": "", "no_format": None})
            else:
                line["columns"][tax_col_idx].update({"no_format": tax_total})

        return lines



