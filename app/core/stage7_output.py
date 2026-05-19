"""Stage 7 — Excel 산출 + 동결 (doc/03-tc-schema.md §6)."""
from __future__ import annotations
from pathlib import Path
from typing import Callable

from app.tools.excel_builder import build as build_excel


def output(
    tcs: list[dict],
    run_dir: Path,
    progress_cb: Callable[[str], None] | None = None,
) -> Path:
    """tc_final.xlsx 생성 후 경로 반환."""
    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    _cb("Stage 7: Excel 산출 중")
    out_path = run_dir / "tc_final.xlsx"
    build_excel(tcs, out_path)
    _cb(f"Stage 7 완료 → {out_path}")
    return out_path
