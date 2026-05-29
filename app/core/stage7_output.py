"""Stage 7 — Excel 산출 + 동결 (doc/03-tc-schema.md §6)."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Callable

from app.tools.excel_builder import build as build_excel


def output(
    tcs: list[dict],
    run_dir: Path,
    progress_cb: Callable[[str], None] | None = None,
) -> Path:
    """tc_final.xlsx 생성 후 경로 반환.

    run_dir/meta.json 이 있으면 '제한사항' 시트를 추가 (박정훈 시험 인증 권고).
    """
    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    _cb("Stage 7: Excel 산출 중")

    # meta.json 로드 (없거나 파싱 실패 시 None → 제한사항 시트 생략)
    meta: dict | None = None
    meta_path = run_dir / "meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = None

    out_path = run_dir / "tc_final.xlsx"
    build_excel(tcs, out_path, meta=meta)
    _cb(f"Stage 7 완료 → {out_path}")
    return out_path
