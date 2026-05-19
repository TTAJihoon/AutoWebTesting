"""Stage 2 — leaf별 TC 설계 (LLM TC_DESIGN 호출)."""
from __future__ import annotations
from typing import Callable

from app.core.stage1_ingest import excerpt_for_leaf

_DEFECT_PATTERNS_DEFAULT = (
    "F-1: 입력 길이 검증 누락 / F-2: 권한 우회 (타인 리소스 접근) / "
    "F-3: 페이지 경계값 처리 누락 / F-4: 빈 입력 미처리"
)


def design(
    leaves: list[dict],
    manual_text: str,
    llm_client,
    defect_patterns: str = _DEFECT_PATTERNS_DEFAULT,
    progress_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """모든 leaf에 대해 TC를 생성해 단일 리스트로 반환."""
    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    all_tcs: list[dict] = []
    tc_counter = 1

    for leaf_idx, leaf in enumerate(leaves, 1):
        leaf_num = f"{leaf_idx:03d}"
        tc_id_start = f"TC-{leaf_num}-001"
        excerpt = excerpt_for_leaf(manual_text, leaf)

        _cb(f"TC 설계 중 ({leaf_idx}/{len(leaves)}): {leaf['category_leaf']}")

        result = llm_client.call("TC_DESIGN", {
            "category_major": leaf["category_major"],
            "category_mid": leaf["category_mid"],
            "category_leaf": leaf["category_leaf"],
            "requirement_id": leaf["requirement_id"],
            "tc_id_start": tc_id_start,
            "manual_excerpt": excerpt[:1500],
            "defect_patterns": defect_patterns[:500],
        })

        for tc in result.get("tcs", []):
            # 프롬프트 출력 필드 → 내부 스키마 필드 정규화
            if "expected_output" in tc and "expected" not in tc:
                tc["expected"] = tc.pop("expected_output")
            if "technique" in tc and "design_technique" not in tc:
                tc["design_technique"] = tc.pop("technique")
            # G1 필드 보강
            tc["대분류"] = leaf["category_major"]
            tc["중분류"] = leaf["category_mid"]
            tc["소분류"] = leaf["category_leaf"]
            tc["requirement_id"] = leaf["requirement_id"]
            # G4 초기화
            tc.setdefault("review_status", "pending")
            tc.setdefault("reviewer_note", "")
            tc.setdefault("reviewer_id", "")
            # G5 초기화
            tc.setdefault("actual", "")
            tc.setdefault("result", "not_executed")
            tc.setdefault("failure_reason", "")
            tc.setdefault("exec_confidence", 0.0)
            all_tcs.append(tc)

    _cb(f"Stage 2 완료 — TC {len(all_tcs)}개 생성")
    return all_tcs
