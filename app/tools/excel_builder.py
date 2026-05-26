"""TC Excel 산출 빌더 (Stage 7, doc/03-tc-schema.md §6)."""
from __future__ import annotations
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# 컬럼 정의 (doc/03-tc-schema.md §2)
_SHEET1_COLS = [
    "tc_id", "대분류", "중분류", "소분류", "scenario",
    "precondition", "expected", "actual", "result", "failure_reason",
]
_META_COLS = [
    "tc_id", "requirement_id", "design_technique", "source_quote",
    "gen_confidence", "exec_confidence",
    "review_status", "reviewer_note", "reviewer_id",
]

_CONFIDENCE_FILLS = {
    "high":   PatternFill(fill_type="solid", fgColor="C6EFCE"),  # 연두
    "mid":    PatternFill(fill_type="solid", fgColor="FFEB9C"),  # 노랑
    "low":    PatternFill(fill_type="solid", fgColor="FFC7CE"),  # 빨강
}

_RESULT_FILLS = {
    "pass":    PatternFill(fill_type="solid", fgColor="C6EFCE"),
    "fail":    PatternFill(fill_type="solid", fgColor="FFC7CE"),
    "blocked": PatternFill(fill_type="solid", fgColor="FFEB9C"),
}

_THIN = Side(style="thin")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)


def _header_style(cell, fill_color: str = "4472C4"):
    cell.fill = PatternFill(fill_type="solid", fgColor=fill_color)
    cell.font = Font(bold=True, color="FFFFFF", size=10)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = _BORDER


def _write_sheet(ws, columns: list[str], rows: list[dict], confidence_col: str | None = None):
    ws.freeze_panes = "A2"
    for ci, col in enumerate(columns, 1):
        cell = ws.cell(row=1, column=ci, value=col)
        _header_style(cell)
        ws.column_dimensions[get_column_letter(ci)].width = max(12, len(col) + 4)

    for ri, row in enumerate(rows, 2):
        for ci, col in enumerate(columns, 1):
            val = row.get(col, "")
            cell = ws.cell(row=ri, column=ci, value=val)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = _BORDER

            if col == "result" and isinstance(val, str):
                fill = _RESULT_FILLS.get(val.lower())
                if fill:
                    cell.fill = fill

            if col == confidence_col and isinstance(val, (int, float)):
                if val >= 0.85:
                    cell.fill = _CONFIDENCE_FILLS["high"]
                elif val >= 0.50:
                    cell.fill = _CONFIDENCE_FILLS["mid"]
                else:
                    cell.fill = _CONFIDENCE_FILLS["low"]

    ws.auto_filter.ref = ws.dimensions


def build(tcs: list[dict], output_path: str | Path) -> Path:
    """TC 목록을 받아 tc_final.xlsx 를 생성하고 경로를 반환."""
    wb = Workbook()

    ws1 = wb.active
    ws1.title = "표준 양식"
    _write_sheet(ws1, _SHEET1_COLS, tcs)

    ws2 = wb.create_sheet("AWT_Meta")
    _write_sheet(ws2, _META_COLS, tcs, confidence_col="gen_confidence")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    return out


def build_review(tcs: list[dict], output_path: str | Path) -> Path:
    """Reviewer Gate용 xlsx (Stage 4 전 단계)."""
    review_cols = _SHEET1_COLS[:7] + ["design_technique", "source_quote", "gen_confidence", "review_status", "reviewer_note"]

    wb = Workbook()
    ws = wb.active
    ws.title = "TC 검토"
    _write_sheet(ws, review_cols, tcs, confidence_col="gen_confidence")

    # 드롭다운 (review_status 컬럼) — TC가 1개 이상일 때만 설정
    # len(tcs)==0 이면 sqref="K2:K1" → min_row>max_row → openpyxl ValueError
    if tcs:
        from openpyxl.worksheet.datavalidation import DataValidation
        status_col_idx = review_cols.index("review_status") + 1
        status_col_letter = get_column_letter(status_col_idx)
        dv = DataValidation(type="list", formula1='"approved,edited,rejected,pending"', allow_blank=False)
        ws.add_data_validation(dv)
        dv.sqref = f"{status_col_letter}2:{status_col_letter}{len(tcs) + 1}"

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    return out
