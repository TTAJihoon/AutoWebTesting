"""Stage 2 — leaf별 TC 설계 (LLM TC_DESIGN v2.1 호출).

v2.1 변경 (D49): negative_categories 입력 추가 — leaf 유형별 음성 카테고리 강제.
"""
from __future__ import annotations
from typing import Callable

from app.core.stage1_ingest import excerpt_for_leaf
from app.assets.invariants_loader import load_invariants_multi, format_for_llm as fmt_invariants
from app.assets.defect_catalog import search_similar_defects, format_for_llm as fmt_defects
from app.assets.product_types import classify_product_types
from app.validation.v10_negative_coverage import applicable_categories_for_leaf


# D49 — LLM 프롬프트용 카테고리 짧은 설명
_CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "validation_failure":    "입력 형식·필수값 위반 (이메일 형식, 빈 필드, 길이 미달)",
    "duplicate_or_conflict": "중복·동시성·충돌 (중복 아이디, 동시 수정, 이미 존재하는 키)",
    "permission_denied":     "권한 거부 (비로그인, 권한 없는 사용자, 만료 토큰)",
    "boundary_violation":    "경계값 초과 (최대 길이 +1, 0/음수, 파일 크기 상한 초과)",
    "injection_or_security": "보안 공격 패턴 (SQL injection, XSS, Path traversal, CSRF)",
}


def _format_negative_categories(leaf_name: str) -> str:
    """leaf에 적용되는 negative 카테고리를 LLM 입력용 텍스트로 포맷."""
    cats = applicable_categories_for_leaf(leaf_name)
    if not cats:
        return "(이 leaf는 음성 카테고리 강제 대상이 아닙니다 — negative_category=null 허용)"
    lines = [f"이 leaf에서 강제 적용해야 하는 음성 카테고리 (각 ≥ 1 TC):"]
    for c in cats:
        lines.append(f"- {c}: {_CATEGORY_DESCRIPTIONS[c]}")
    return "\n".join(lines)

# featureType 추정 (leaf category → featureType 매핑)
_FEATURE_TYPE_MAP: dict[str, str] = {
    "등록": "CREATE", "작성": "CREATE", "추가": "CREATE", "생성": "CREATE",
    "수정": "UPDATE", "편집": "UPDATE", "변경": "UPDATE",
    "삭제": "DELETE", "제거": "DELETE",
    "조회": "READ", "목록": "READ", "검색": "SEARCH", "페이지": "PAGINATION",
    "로그인": "AUTH", "로그아웃": "AUTH", "인증": "AUTH", "권한": "PERMISSION",
}


def _guess_feature_type(leaf_name: str) -> str:
    for keyword, ftype in _FEATURE_TYPE_MAP.items():
        if keyword in leaf_name:
            return ftype
    return "OTHER"


def design(
    leaves: list[dict],
    manual_text: str,
    llm_client,
    defect_patterns: str = "",  # 하위 호환 (사용 안 함, 자산에서 로드)
    progress_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """모든 leaf에 대해 TC를 생성해 단일 리스트로 반환."""
    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    # 제품 유형 분류 (전체 매뉴얼 기준)
    product_type_ids = classify_product_types(manual_text)
    invariants = load_invariants_multi(product_type_ids)

    all_tcs: list[dict] = []

    for leaf_idx, leaf in enumerate(leaves, 1):
        leaf_num = f"{leaf_idx:03d}"
        tc_id_start = f"TC-{leaf_num}-001"
        excerpt = excerpt_for_leaf(manual_text, leaf)
        feature_type = _guess_feature_type(leaf["category_leaf"])

        # 자산 주입: invariants + 유사 결함
        invariants_text = fmt_invariants(invariants, feature_type=feature_type)
        similar_defects = search_similar_defects(product_type_ids, feature_type, top_k=3)
        defects_text = fmt_defects(similar_defects)

        _cb(f"TC 설계 중 ({leaf_idx}/{len(leaves)}): {leaf['category_leaf']}")

        result = llm_client.call("TC_DESIGN", {
            "category_major": leaf["category_major"],
            "category_mid": leaf["category_mid"],
            "category_leaf": leaf["category_leaf"],
            "requirement_id": leaf["requirement_id"],
            "tc_id_start": tc_id_start,
            "manual_excerpt": excerpt[:1500],
            "domain_invariants": invariants_text or "(없음)",
            "similar_past_defects": defects_text or "(없음)",
            "negative_categories": _format_negative_categories(leaf["category_leaf"]),
        })

        for tc_idx, tc in enumerate(result.get("tcs", []), 1):
            # 프롬프트 출력 필드 → 내부 스키마 필드 정규화
            if "expected_output" in tc and "expected" not in tc:
                tc["expected"] = tc.pop("expected_output")
            if "technique" in tc and "design_technique" not in tc:
                tc["design_technique"] = tc.pop("technique")
            # tc_id 강제 정규화 — LLM이 형식을 틀리거나 서픽스를 붙여도 덮어씀
            # TC-{leaf_num:03d}-{tc_idx:03d} 형식 보장 (예: TC-001-003)
            tc["tc_id"] = f"TC-{leaf_num}-{tc_idx:03d}"
            # G1 필드 보강
            tc["대분류"]          = leaf["category_major"]
            tc["중분류"]          = leaf["category_mid"]
            tc["소분류"]          = leaf["category_leaf"]
            tc["requirement_id"]  = leaf["requirement_id"]
            tc["screenshot_file"] = leaf.get("screenshot_file", "")  # Stage 0 스크린샷 연결
            # G4 초기화
            tc.setdefault("review_status", "pending")
            tc.setdefault("reviewer_note", "")
            tc.setdefault("reviewer_id", "")
            # G5 초기화
            tc.setdefault("actual", "")
            tc.setdefault("result", "not_executed")
            tc.setdefault("failure_reason", "")
            tc.setdefault("exec_confidence", 0.0)
            tc.setdefault("failure_category", "")
            tc.setdefault("failure_category_source", "")
            # G6 — negative_category (D49)
            # negative_* 기법은 negative_category 필수, 그 외는 null/빈값
            if tc.get("design_technique", "").startswith("negative_"):
                tc.setdefault("negative_category", "")
            else:
                tc.setdefault("negative_category", None)
            all_tcs.append(tc)

    _cb(f"Stage 2 완료 - TC {len(all_tcs)}개 생성")
    return all_tcs
