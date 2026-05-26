"""TC Excel 산출 빌더 (Stage 7, doc/03-tc-schema.md §6)."""
from __future__ import annotations
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# 컬럼 정의 (doc/03-tc-schema.md §2)
# screenshot_file: Stage 0 스크린샷과 TC 연결 (파일명만 저장, 절대경로 아님)
_SHEET1_COLS = [
    "tc_id", "대분류", "중분류", "소분류", "scenario",
    "precondition", "expected", "actual", "result", "failure_reason",
    "screenshot_file",
]
_META_COLS = [
    "tc_id", "requirement_id", "design_technique", "source_quote",
    "gen_confidence", "exec_confidence",
    "review_status", "reviewer_note", "reviewer_id",
    "screenshot_file",
]

# 기능 목록 컬럼 (Stage 0 DOM 스캔 결과)
_FEATURE_COLS = [
    "category_major", "category_mid", "category_leaf",
    "implicit_spec", "source_element", "confidence", "screenshot_file",
]
_FEATURE_COL_NAMES = {
    "category_major":  "대분류",
    "category_mid":    "중분류",
    "category_leaf":   "기능명 (소분류)",
    "implicit_spec":   "기능 명세",
    "source_element":  "근거 DOM 요소",
    "confidence":      "신뢰도",
    "screenshot_file": "관련 스크린샷",
}
# 컬럼별 권장 너비 (기능목록 시트용)
_FEATURE_COL_WIDTHS = {
    "category_major":  16,
    "category_mid":    18,
    "category_leaf":   22,
    "implicit_spec":   45,
    "source_element":  28,
    "confidence":      12,
    "screenshot_file": 30,
}

_CONFIDENCE_FILLS = {
    "high": PatternFill(fill_type="solid", fgColor="C6EFCE"),  # 연두
    "mid":  PatternFill(fill_type="solid", fgColor="FFEB9C"),  # 노랑
    "low":  PatternFill(fill_type="solid", fgColor="FFC7CE"),  # 빨강
}

_RESULT_FILLS = {
    "pass":    PatternFill(fill_type="solid", fgColor="C6EFCE"),
    "fail":    PatternFill(fill_type="solid", fgColor="FFC7CE"),
    "blocked": PatternFill(fill_type="solid", fgColor="FFEB9C"),
}

_THIN   = Side(style="thin")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)


def _header_style(cell, fill_color: str = "4472C4"):
    cell.fill      = PatternFill(fill_type="solid", fgColor=fill_color)
    cell.font      = Font(bold=True, color="FFFFFF", size=10)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border    = _BORDER


def _write_sheet(ws, columns: list[str], rows: list[dict], confidence_col: str | None = None):
    ws.freeze_panes = "A2"
    for ci, col in enumerate(columns, 1):
        cell = ws.cell(row=1, column=ci, value=col)
        _header_style(cell)
        ws.column_dimensions[get_column_letter(ci)].width = max(12, len(col) + 4)

    for ri, row in enumerate(rows, 2):
        for ci, col in enumerate(columns, 1):
            val  = row.get(col, "")
            cell = ws.cell(row=ri, column=ci, value=val)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border    = _BORDER

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


# ── TC Excel (Stage 7 최종 산출) ──────────────────────────────────────────────

def build(tcs: list[dict], output_path: str | Path) -> Path:
    """TC 목록을 받아 tc_final.xlsx 를 생성하고 경로를 반환."""
    wb = Workbook()

    ws1 = wb.active
    ws1.title = "표준 양식"
    _write_sheet(ws1, _SHEET1_COLS, tcs)
    # screenshot_file 열 너비 조정
    sf_col = get_column_letter(_SHEET1_COLS.index("screenshot_file") + 1)
    ws1.column_dimensions[sf_col].width = 30

    ws2 = wb.create_sheet("AWT_Meta")
    _write_sheet(ws2, _META_COLS, tcs, confidence_col="gen_confidence")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    return out


def build_review(tcs: list[dict], output_path: str | Path) -> Path:
    """Reviewer Gate용 xlsx (Stage 4 전 단계)."""
    review_cols = (
        _SHEET1_COLS[:7]
        + ["design_technique", "source_quote", "gen_confidence",
           "review_status", "reviewer_note", "screenshot_file"]
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "TC 검토"
    _write_sheet(ws, review_cols, tcs, confidence_col="gen_confidence")

    # screenshot_file 열 너비
    if "screenshot_file" in review_cols:
        sf_col = get_column_letter(review_cols.index("screenshot_file") + 1)
        ws.column_dimensions[sf_col].width = 30

    # 드롭다운 (review_status 컬럼) — TC가 1개 이상일 때만 설정
    # len(tcs)==0 이면 sqref="K2:K1" → min_row>max_row → openpyxl ValueError
    if tcs:
        from openpyxl.worksheet.datavalidation import DataValidation
        status_col_idx    = review_cols.index("review_status") + 1
        status_col_letter = get_column_letter(status_col_idx)
        dv = DataValidation(
            type="list",
            formula1='"approved,edited,rejected,pending"',
            allow_blank=False,
        )
        ws.add_data_validation(dv)
        dv.sqref = f"{status_col_letter}2:{status_col_letter}{len(tcs) + 1}"

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    return out


# ── 기능 목록 Excel (Stage 0 DOM 스캔 결과) ───────────────────────────────────

def build_features(features: list[dict], output_path: str | Path) -> Path:
    """Stage 0 기능 목록을 Excel로 저장.

    Args:
        features: feature-spec-draft.json 의 'features' 리스트
        output_path: 저장 경로 (.xlsx)
    Returns:
        저장된 파일 경로
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "기능 목록"
    ws.freeze_panes = "A2"

    # 헤더
    for ci, col in enumerate(_FEATURE_COLS, 1):
        cell = ws.cell(row=1, column=ci, value=_FEATURE_COL_NAMES.get(col, col))
        _header_style(cell, fill_color="1F4E79")  # 진한 남색 — TC Excel과 구분
        ws.column_dimensions[get_column_letter(ci)].width = _FEATURE_COL_WIDTHS.get(col, 16)

    # 데이터
    for ri, feat in enumerate(features, 2):
        for ci, col in enumerate(_FEATURE_COLS, 1):
            val  = feat.get(col, "")
            cell = ws.cell(row=ri, column=ci, value=val)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border    = _BORDER

            # confidence 색상 (HIGH/MID/INFERRED)
            if col == "confidence" and isinstance(val, str):
                val_upper = val.upper()
                if val_upper == "HIGH":
                    cell.fill = _CONFIDENCE_FILLS["high"]
                elif val_upper == "MID":
                    cell.fill = _CONFIDENCE_FILLS["mid"]
                elif val_upper == "INFERRED":
                    cell.fill = _CONFIDENCE_FILLS["low"]

    ws.auto_filter.ref = ws.dimensions

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    return out
