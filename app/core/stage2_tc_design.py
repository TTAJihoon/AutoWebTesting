"""Stage 2 — leaf별 TC 설계 (LLM TC_DESIGN v2.1 호출).

v2.1 변경 (D49): negative_categories 입력 추가 — leaf 유형별 음성 카테고리 강제.
"""
from __future__ import annotations
from collections import OrderedDict
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


_CONFIDENCE_ORDER = {"HIGH": 0, "MID": 1, "INFERRED": 2, "": 3}

# D54 — 그룹(페이지)당 한 번에 설계할 leaf 최대 수 (토큰 예산 보호)
_GROUP_CAP = 12


def _prioritize_leaves(leaves: list[dict], max_leaves: int) -> list[dict]:
    """신뢰도(HIGH→MID→INFERRED) 우선 정렬 후 max_leaves 개수로 자름.
    max_leaves=0이면 자르지 않음.
    """
    if max_leaves <= 0 or len(leaves) <= max_leaves:
        return leaves
    sorted_leaves = sorted(
        leaves,
        key=lambda lf: _CONFIDENCE_ORDER.get(
            str(lf.get("confidence", "")).upper(), 3
        ),
    )
    return sorted_leaves[:max_leaves]


def design(
    leaves: list[dict],
    manual_text: str,
    llm_client,
    defect_patterns: str = "",  # 하위 호환 (사용 안 함, 자산에서 로드)
    max_leaves: int = 0,        # 0 = 무제한; >0이면 신뢰도 우선으로 상위 N개만 처리
    progress_cb: Callable[[str], None] | None = None,
    failed_leaves_out: list[dict] | None = None,    # 추적성용: 실패한 leaf 정보 기록처
    excluded_leaves_out: list[dict] | None = None,  # 추적성용: max_leaves cap으로 제외된 leaf
    should_stop: Callable[[], bool] | None = None,  # 사용자 중단 신호 (협력적)
) -> list[dict]:
    """모든 leaf에 대해 TC를 생성해 단일 리스트로 반환.

    Args:
        failed_leaves_out:   리스트 전달 시 분석 실패한 leaf의 {idx, name, reason}을 append.
        excluded_leaves_out: 리스트 전달 시 max_leaves cap으로 잘린 leaf의 {idx, name, confidence}을 append.
    """
    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    # max_leaves 적용 (API 비용·무료 쿼터 보호)
    original_count = len(leaves)

    # ── 안전 가드 (C): max_leaves=0(무제한)인데 leaves가 너무 많으면 자동 제한 ──
    SAFETY_CAP = 100
    leaves_before_cap = list(leaves)   # 추적성: 제외된 leaf 식별용 원본 보관

    if max_leaves <= 0 and original_count > SAFETY_CAP:
        leaves = _prioritize_leaves(leaves, SAFETY_CAP)
        _cb(
            f"⚠ leaf {original_count}개 → 안전 제한 {SAFETY_CAP}개 자동 적용 "
            f"(max_leaves=0). 무제한 실행이 필요하면 max_leaves를 명시적 큰 값(예: 9999)으로 설정하세요."
        )
    elif max_leaves > 0:
        leaves = _prioritize_leaves(leaves, max_leaves)
        if original_count > max_leaves:
            _cb(
                f"TC 설계 대상 leaf {original_count}개 → 상위 {len(leaves)}개로 제한 "
                f"(max_leaves={max_leaves}; 해제하려면 설정에서 0으로 변경)"
            )

    # 추적성: max_leaves cap으로 제외된 leaf 목록 기록
    if excluded_leaves_out is not None and len(leaves) < len(leaves_before_cap):
        included_names = {lf.get("category_leaf") for lf in leaves}
        for i, lf in enumerate(leaves_before_cap, 1):
            if lf.get("category_leaf") not in included_names:
                excluded_leaves_out.append({
                    "idx":        i,
                    "name":       lf.get("category_leaf", ""),
                    "confidence": str(lf.get("confidence", "")),
                    "source_url": lf.get("source_url", ""),
                })

    # 제품 유형 분류 (전체 매뉴얼 기준)
    product_type_ids = classify_product_types(manual_text)
    invariants = load_invariants_multi(product_type_ids)

    all_tcs: list[dict] = []
    failed_leaves: list[tuple[int, str, str]] = []   # (leaf_num, leaf명, 오류요약)

    # ── D54: 페이지(source_url) 단위 그룹핑 + cap 서브배치 ──────────────────
    # leaf 1개씩이 아니라 같은 화면 기능을 묶어 TC_DESIGN_GROUP 1회 호출 →
    # LLM이 기능 관계를 보고(중복↓·cross_feature↑) 호출 수도 급감.
    indexed = list(enumerate(leaves, 1))            # (leaf_num, leaf) — tc_id용 안정 번호
    groups: "OrderedDict[str, list]" = OrderedDict()
    for leaf_num, leaf in indexed:
        url = leaf.get("source_url") or "(미상)"
        groups.setdefault(url, []).append((leaf_num, leaf))
    batches: list[tuple[str, list]] = []
    for url, members in groups.items():
        for i in range(0, len(members), _GROUP_CAP):
            batches.append((url, members[i:i + _GROUP_CAP]))

    _cb(f"TC 설계 — 기능 {len(leaves)}개를 {len(batches)}개 그룹(페이지 단위)으로 설계")

    per_leaf_seq: dict[int, int] = {}   # leaf_num -> 다음 TC 일련번호

    def _finalize(tc: dict, leaf: dict, leaf_num: int) -> dict:
        """LLM 출력 TC를 내부 스키마로 정규화 + 소속 leaf 필드 부여."""
        if "expected_output" in tc and "expected" not in tc:
            tc["expected"] = tc.pop("expected_output")
        if "technique" in tc and "design_technique" not in tc:
            tc["design_technique"] = tc.pop("technique")
        tc.pop("leaf_index", None)
        seq = per_leaf_seq.get(leaf_num, 0) + 1
        per_leaf_seq[leaf_num] = seq
        tc["tc_id"]           = f"TC-{leaf_num:03d}-{seq:03d}"
        tc["대분류"]          = leaf.get("category_major", "")
        tc["중분류"]          = leaf.get("category_mid", "")
        tc["소분류"]          = leaf.get("category_leaf", "")
        tc["requirement_id"]  = leaf.get("requirement_id", "")
        tc["screenshot_file"] = leaf.get("screenshot_file", "")   # Stage 0 스크린샷 연결
        tc.setdefault("review_status", "pending")
        tc.setdefault("reviewer_note", "")
        tc.setdefault("reviewer_id", "")
        tc.setdefault("actual", "")
        tc.setdefault("result", "not_executed")
        tc.setdefault("failure_reason", "")
        tc.setdefault("exec_confidence", 0.0)
        tc.setdefault("failure_category", "")
        tc.setdefault("failure_category_source", "")
        if (tc.get("design_technique", "") or "").startswith("negative_"):
            tc.setdefault("negative_category", "")
        else:
            tc.setdefault("negative_category", None)
        return tc

    for b_idx, (url, members) in enumerate(batches, 1):
        # 사용자 중단 협력 체크 (다음 그룹 시작 전)
        if should_stop and should_stop():
            _cb(f"⏹ 사용자 중단 — TC 설계 종료 ({b_idx-1}/{len(batches)} 그룹, TC {len(all_tcs)}개)")
            break

        # 그룹 공통 자산: 멤버들의 feature_type union
        ftypes: list[str] = []
        for _, leaf in members:
            ft = _guess_feature_type(leaf.get("category_leaf", ""))
            if ft not in ftypes:
                ftypes.append(ft)
        inv_parts, def_parts = [], []
        for ft in ftypes:
            t = fmt_invariants(invariants, feature_type=ft)
            if t and t not in inv_parts:
                inv_parts.append(t)
            dt = fmt_defects(search_similar_defects(product_type_ids, ft, top_k=2))
            if dt and dt not in def_parts:
                def_parts.append(dt)
        invariants_text = "\n".join(inv_parts)
        defects_text    = "\n".join(def_parts)

        # 기능 목록 블록 (그룹-로컬 1-based 번호)
        lines = []
        for gi, (leaf_num, leaf) in enumerate(members, 1):
            excerpt = excerpt_for_leaf(manual_text, leaf)[:400]
            negcats = _format_negative_categories(leaf.get("category_leaf", ""))
            lines.append(
                f"{gi}. [{leaf.get('category_major','')} > {leaf.get('category_mid','')} > "
                f"{leaf.get('category_leaf','')}] (req={leaf.get('requirement_id','')})\n"
                f"   명세: {excerpt or '(없음)'}\n"
                f"   {negcats}"
            )
        features_block = "\n".join(lines)
        page_context   = f"{url}  (기능 {len(members)}개)"

        _cb(f"TC 설계 중 (그룹 {b_idx}/{len(batches)}): {url} — 기능 {len(members)}개")

        # ── 그룹 실패 허용 — 한 그룹이 실패해도 다음 그룹으로 진행 ──
        try:
            result = llm_client.call("TC_DESIGN_GROUP", {
                "page_context":         page_context,
                "features_block":       features_block,
                "domain_invariants":    invariants_text or "(없음)",
                "similar_past_defects": defects_text or "(없음)",
            })
        except Exception as e:
            err_msg = str(e).splitlines()[0][:200]
            for leaf_num, leaf in members:
                failed_leaves.append((leaf_num, leaf.get("category_leaf", ""), err_msg))
                if failed_leaves_out is not None:
                    failed_leaves_out.append({
                        "idx": leaf_num, "name": leaf.get("category_leaf", ""), "reason": err_msg,
                    })
            _cb(f"⚠ 그룹 분석 실패 ({b_idx}/{len(batches)}): {url} — {err_msg}")
            if "일일 쿼터" in err_msg or "PerDay" in err_msg:
                _cb(f"⚠ 일일 쿼터 초과로 Stage 2 조기 종료 — TC {len(all_tcs)}개")
                break
            continue

        # leaf_index(그룹-로컬 1-based) → (leaf_num, leaf) 매핑
        for tc in result.get("tcs", []):
            try:
                gi = int(tc.get("leaf_index", 1))
            except (TypeError, ValueError):
                gi = 1
            if gi < 1 or gi > len(members):
                gi = 1
            leaf_num, leaf = members[gi - 1]
            all_tcs.append(_finalize(tc, leaf, leaf_num))

    if failed_leaves:
        _cb(
            f"Stage 2 완료 - TC {len(all_tcs)}개 생성 "
            f"(분석 실패 leaf {len(failed_leaves)}개)"
        )
    else:
        _cb(f"Stage 2 완료 - TC {len(all_tcs)}개 생성")
    return all_tcs
