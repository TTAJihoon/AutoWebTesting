"""Stage 1 — 입력 파일 파싱·정규화 → leaf 목록 추출."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Callable

from app.tools.file_parser import parse


def ingest(
    files: list[str | Path],
    run_dir: Path,
    feature_spec: dict | None = None,
    progress_cb: Callable[[str], None] | None = None,
) -> dict:
    """파일 목록을 파싱해 매뉴얼 텍스트와 leaf 목록을 반환.

    Returns:
        {
            "manual_text": str,
            "leaves": [{"requirement_id": str, "category_major": str,
                        "category_mid": str, "category_leaf": str}],
        }
    """
    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    out_dir = run_dir / "ingest"
    out_dir.mkdir(parents=True, exist_ok=True)

    texts: list[str] = []
    for f in files:
        _cb(f"파싱 중: {Path(f).name}")
        texts.append(parse(f))

    manual_text = "\n\n".join(texts)
    (out_dir / "manual.txt").write_text(manual_text, encoding="utf-8")

    # leaf 목록 구성
    leaves: list[dict] = []

    # Stage 0 결과 있으면 우선 사용
    if feature_spec and feature_spec.get("features"):
        for i, feat in enumerate(feature_spec["features"], 1):
            leaves.append({
                "requirement_id": f"F{i:03d}",
                "category_major": feat.get("category_major", ""),
                "category_mid": feat.get("category_mid", ""),
                "category_leaf": feat.get("category_leaf", ""),
            })
    else:
        # 파일에서 기능 목록 추출 (마크다운 헤더 기반 휴리스틱)
        leaves = _extract_leaves_from_text(manual_text)

    _cb(f"Stage 1 완료 — leaf {len(leaves)}개")
    return {"manual_text": manual_text, "leaves": leaves}


def _extract_leaves_from_text(text: str) -> list[dict]:
    """마크다운/텍스트에서 계층형 기능 목록 추출 (휴리스틱)."""
    leaves: list[dict] = []
    major = mid = leaf = ""
    idx = 0

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            leaf = stripped[4:].strip()
            if major and mid and leaf:
                idx += 1
                leaves.append({
                    "requirement_id": f"F{idx:03d}",
                    "category_major": major,
                    "category_mid": mid,
                    "category_leaf": leaf,
                })
        elif stripped.startswith("## "):
            mid = stripped[3:].strip()
            leaf = ""
        elif stripped.startswith("# "):
            major = stripped[2:].strip()
            mid = leaf = ""

    # 헤더가 없으면 섹션 전체를 leaf 1개로
    if not leaves and text.strip():
        leaves.append({
            "requirement_id": "F001",
            "category_major": "전체 기능",
            "category_mid": "일반",
            "category_leaf": "기능 전체",
        })
    return leaves


def excerpt_for_leaf(manual_text: str, leaf: dict, max_chars: int = 1500) -> str:
    """매뉴얼에서 해당 leaf 관련 섹션 발췌 (V2 근거 확보)."""
    keyword = leaf.get("category_leaf", "") or leaf.get("category_mid", "")
    if not keyword:
        return manual_text[:max_chars]

    idx = manual_text.find(keyword)
    if idx == -1:
        return manual_text[:max_chars]

    start = max(0, idx - 200)
    end = min(len(manual_text), idx + max_chars - 200)
    return manual_text[start:end]
