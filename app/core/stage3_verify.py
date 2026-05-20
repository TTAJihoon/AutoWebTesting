"""Stage 3 — V1~V10 검증 + 실패 시 TC_REGEN 재호출 (doc/03-tc-schema.md §5).

V10 추가 (D49): negative 카테고리 커버리지 강제.

아키텍처 노트 (Bug-1 수정):
  V10 실패 tc_id = "LEAF:F001" 형식 → 실제 TC id와 매칭 안 됨.
  V10은 기존 TC를 고치는 게 아니라 누락 카테고리 TC를 *추가* 해야 하므로
  TC_REGEN 루프에서 분리, _add_v10_tcs()로 별도 처리.
"""
from __future__ import annotations
import re
from typing import Callable

from app.validation import v10_negative_coverage

_REQUIRED_COLS = [
    "tc_id", "대분류", "중분류", "소분류", "scenario",
    "precondition", "expected", "requirement_id",
    "design_technique", "source_quote", "gen_confidence",
]
_VALID_TECHNIQUES = {
    "happy_path", "equivalence", "boundary",
    "negative_basic", "negative_deep", "state_transition", "cross_feature",
}
_TC_ID_RE = re.compile(r"^TC-\d{3}-\d{3}$")

# V3 INFERRED 임계 (PoC 결과 30% 완화, 실제 OSS 10% 재강제)
INFERRED_THRESHOLD = 0.30
# V10 최소 카테고리 커버리지 (D49)
NEGATIVE_COVERAGE_MIN = 0.6


_REGEN_BATCH_SIZE = 10   # V3 REGEN: 한 번에 처리할 최대 TC 수
_REGEN_TC_JSON_LIMIT = 6000  # failed_tcs_json 문자 한계


def verify(
    tcs: list[dict],
    manual_text: str,
    llm_client,
    leaves: list[dict],
    max_retries: int = 3,
    inferred_threshold: float = INFERRED_THRESHOLD,
    progress_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """V1~V5 검증. 실패 TC는 재호출(최대 max_retries회). 최종 TC 목록 반환."""
    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    for attempt in range(1, max_retries + 1):
        all_failures = _check_all(tcs, manual_text, leaves, inferred_threshold)

        # V10 (카테고리 추가) vs 구조적 오류 (V1-V5, TC_REGEN 대상) 분리
        structural = [f for f in all_failures if f["v"] != "V10"]
        v10_gaps   = [f for f in all_failures if f["v"] == "V10"]

        if not structural:
            # 구조적 오류 없음 — V10 gap만 남은 경우 TC 추가 후 완료
            if v10_gaps:
                _cb(f"  V10 커버리지 부족 {len(v10_gaps)}개 leaf — 누락 카테고리 TC 추가 생성")
                new_tcs = _add_v10_tcs(v10_gaps, leaves, manual_text, tcs, llm_client, _cb)
                tcs.extend(new_tcs)
            _cb(f"Stage 3 완료 (시도 {attempt}회) — 모든 검증 통과")
            return tcs

        # V1-V5 구조적 실패 → TC_REGEN
        _cb(f"  구조적 실패 {len(structural)}건 (시도 {attempt}/{max_retries}) — TC_REGEN 호출")
        failed_ids  = {f["tc_id"] for f in structural}

        # "ALL" 실패(V3/V4/V5)는 tc_id가 "ALL"로 기록됨 → 실제 대상 TC 선별
        has_all_failure = "ALL" in failed_ids
        failed_ids.discard("ALL")

        if has_all_failure:
            vs_all = {f["v"] for f in structural if f["tc_id"] == "ALL"}
            if "V3" in vs_all:
                # V3: INFERRED 비율 초과 → INFERRED TC만 재생성
                # gen_confidence 낮은 순(개선 여지 높은 순) 상위 REGEN_BATCH_SIZE개만 선택
                inferred_tcs = [
                    tc for tc in tcs
                    if _classify_source_quote(str(tc.get("source_quote", ""))) == "inferred"
                ]
                inferred_tcs.sort(key=lambda t: float(t.get("gen_confidence", 0.5)))
                for tc in inferred_tcs[:_REGEN_BATCH_SIZE]:
                    failed_ids.add(tc["tc_id"])
            if "V4" in vs_all:
                # V4: happy_path 비율 초과 → happy_path TC 일부 재생성
                hp_tcs = [tc for tc in tcs if tc.get("design_technique") == "happy_path"]
                for tc in hp_tcs[len(hp_tcs)//2:]:   # 후반 절반만 대상
                    failed_ids.add(tc["tc_id"])
            if "V5" in vs_all:
                # V5: leaf 미커버 → 전체 재생성 (어느 TC를 수정해야 할지 불명확)
                for tc in tcs:
                    failed_ids.add(tc["tc_id"])

        failed_tcs = [tc for tc in tcs if tc.get("tc_id") in failed_ids]

        fix_instructions = _build_fix_instructions(structural)
        # manual_excerpt: failed_tcs의 requirement_id에 해당하는 매뉴얼 발췌문
        manual_excerpt = _extract_manual_for_tcs(failed_tcs, manual_text)
        regen_result = llm_client.call("TC_REGEN", {
            "manual_excerpt":   manual_excerpt[:2000],
            "failed_tcs_json":  str(failed_tcs)[:_REGEN_TC_JSON_LIMIT],
            "v_failures":       str(structural)[:800],
            "fix_instructions": fix_instructions[:400],
        })

        # 재생성된 TC로 교체 + 필드 정규화
        regen_map = {}
        for tc in regen_result.get("tcs", []):
            # TC_REGEN 출력 필드 → 내부 스키마 정규화 (stage2와 동일)
            if "expected_output" in tc and "expected" not in tc:
                tc["expected"] = tc.pop("expected_output")
            if "technique" in tc and "design_technique" not in tc:
                tc["design_technique"] = tc.pop("technique")
            regen_map[tc["tc_id"]] = tc

        for i, tc in enumerate(tcs):
            if tc.get("tc_id") in regen_map:
                tcs[i] = {**tc, **regen_map[tc["tc_id"]]}

    # 최대 재시도 초과 — 구조적 잔여 실패만 INFERRED 마킹
    _cb("Stage 3: 최대 재시도 초과 — 구조적 잔여 실패 TC를 INFERRED 마킹")
    remaining    = _check_all(tcs, manual_text, leaves, inferred_threshold)
    str_remain   = [f for f in remaining if f["v"] != "V10"]
    v10_remain   = [f for f in remaining if f["v"] == "V10"]

    failed_ids = {f["tc_id"] for f in str_remain}
    for tc in tcs:
        if tc.get("tc_id") in failed_ids:
            tc["source_quote"]  = "INFERRED: max_retry_exceeded"
            tc["review_status"] = "pending"

    # V10 gap이 남아 있어도 마지막으로 한 번 TC 추가 시도
    if v10_remain:
        _cb(f"  V10 gap {len(v10_remain)}개 leaf — 최후 TC 추가 시도")
        new_tcs = _add_v10_tcs(v10_remain, leaves, manual_text, tcs, llm_client, _cb)
        tcs.extend(new_tcs)

    return tcs


def _check_all(tcs, manual_text, leaves, inferred_threshold) -> list[dict]:
    failures = []
    failures += _v1(tcs)
    failures += _v2(tcs, manual_text)
    failures += _v3(tcs, inferred_threshold)
    failures += _v4(tcs)
    failures += _v5(tcs, leaves)
    failures += _v10(tcs, leaves)
    return failures


def _add_v10_tcs(
    v10_gaps: list[dict],
    leaves: list[dict],
    manual_text: str,
    existing_tcs: list[dict],
    llm_client,
    _cb,
) -> list[dict]:
    """V10 커버리지 부족 leaf에 누락 카테고리 TC를 추가 생성.

    TC_REGEN 대신 TC_DESIGN을 재호출해 누락 카테고리만 타깃으로 새 TC를 만든다.
    기존 TC와 ID 충돌 방지를 위해 leaf별 최대 번호 + 1로 시작.
    """
    # lazy imports — stage2 유틸 재사용, 순환 의존 방지
    from app.core.stage1_ingest import excerpt_for_leaf
    from app.assets.invariants_loader import load_invariants_multi, format_for_llm as fmt_inv
    from app.assets.defect_catalog import search_similar_defects, format_for_llm as fmt_def
    from app.assets.product_types import classify_product_types
    from app.core.stage2_tc_design import (
        _CATEGORY_DESCRIPTIONS, _guess_feature_type,
    )

    leaf_by_rid = {lf["requirement_id"]: lf for lf in leaves}
    leaf_to_idx = {lf["requirement_id"]: i + 1 for i, lf in enumerate(leaves)}

    # 기존 TC ID 최대 번호 (leaf별)
    existing_max: dict[str, int] = {}
    for tc in existing_tcs:
        rid = tc.get("requirement_id", "")
        m = re.match(r"TC-\d{3}-(\d{3})$", tc.get("tc_id", ""))
        if m and rid:
            existing_max[rid] = max(existing_max.get(rid, 0), int(m.group(1)))

    # 제품 유형·불변 규칙 (공통)
    product_type_ids = classify_product_types(manual_text)
    inv_map = load_invariants_multi(product_type_ids)

    new_tcs: list[dict] = []
    for gap in v10_gaps:
        rid     = gap.get("leaf_rid", "")
        missing = gap.get("missing_categories", [])
        leaf    = leaf_by_rid.get(rid)
        if not leaf or not missing:
            _cb(f"  V10 gap skip (leaf 없음): rid={rid}")
            continue

        leaf_idx  = leaf_to_idx.get(rid, 1)
        leaf_num  = f"{leaf_idx:03d}"
        next_num  = existing_max.get(rid, 0) + 1
        tc_id_start = f"TC-{leaf_num}-{next_num:03d}"

        missing_desc = "\n".join(
            f"- {c}: {_CATEGORY_DESCRIPTIONS.get(c, '')}" for c in missing
        )
        cats_text = (
            f"V10 커버리지 보완 — 아래 카테고리 각 ≥ 1 TC를 추가 생성해야 함:\n"
            f"{missing_desc}"
        )

        feature_type    = _guess_feature_type(leaf["category_leaf"])
        invariants_text = fmt_inv(inv_map, feature_type=feature_type)
        similar_defects = search_similar_defects(product_type_ids, feature_type, top_k=2)
        defects_text    = fmt_def(similar_defects)
        excerpt         = excerpt_for_leaf(manual_text, leaf)

        _cb(f"  V10 보완 TC 생성: {leaf['category_leaf']} 누락={missing}")
        result = llm_client.call("TC_DESIGN", {
            "category_major": leaf["category_major"],
            "category_mid":   leaf["category_mid"],
            "category_leaf":  leaf["category_leaf"],
            "requirement_id": rid,
            "tc_id_start":    tc_id_start,
            "manual_excerpt": excerpt[:1500],
            "domain_invariants":    invariants_text or "(없음)",
            "similar_past_defects": defects_text or "(없음)",
            "negative_categories":  cats_text,
        })

        for tc in result.get("tcs", []):
            # 출력 필드 정규화
            if "expected_output" in tc and "expected" not in tc:
                tc["expected"] = tc.pop("expected_output")
            if "technique" in tc and "design_technique" not in tc:
                tc["design_technique"] = tc.pop("technique")
            # G1
            tc["대분류"]        = leaf["category_major"]
            tc["중분류"]        = leaf["category_mid"]
            tc["소분류"]        = leaf["category_leaf"]
            tc["requirement_id"] = rid
            # G4
            tc.setdefault("review_status", "pending")
            tc.setdefault("reviewer_note", "")
            tc.setdefault("reviewer_id",  "")
            # G5
            tc.setdefault("actual", "")
            tc.setdefault("result", "not_executed")
            tc.setdefault("failure_reason", "")
            tc.setdefault("exec_confidence", 0.0)
            tc.setdefault("failure_category", "")
            tc.setdefault("failure_category_source", "")
            # G6
            if tc.get("design_technique", "").startswith("negative_"):
                tc.setdefault("negative_category", "")
            else:
                tc.setdefault("negative_category", None)
            new_tcs.append(tc)

            # 최대 번호 갱신 (다음 gap 처리 시 충돌 방지)
            m = re.match(r"TC-\d{3}-(\d{3})$", tc.get("tc_id", ""))
            if m:
                existing_max[rid] = max(existing_max.get(rid, 0), int(m.group(1)))

    return new_tcs


def _v10(tcs: list[dict], leaves: list[dict]) -> list[dict]:
    """V10 — D49 negative_category 커버리지 강제."""
    return v10_negative_coverage.verify(
        tcs, leaves, min_coverage=NEGATIVE_COVERAGE_MIN,
    )


def _v1(tcs: list[dict]) -> list[dict]:
    failures = []
    for tc in tcs:
        missing = [c for c in _REQUIRED_COLS if not str(tc.get(c, "")).strip()]
        if missing or not _TC_ID_RE.match(str(tc.get("tc_id", ""))):
            failures.append({"tc_id": tc.get("tc_id", "?"), "v": "V1",
                              "reason": f"필수 컬럼 비어있거나 tc_id 형식 오류: {missing}"})
    return failures


def _classify_source_quote(sq: str) -> str:
    """source_quote를 3단계로 분류: 'manual' | 'invariants' | 'inferred'"""
    if sq.startswith("INFERRED"):
        return "inferred"
    if sq.startswith("INVARIANT:") or sq.startswith("DEFECT:"):
        return "invariants"
    return "manual"


def _v2(tcs: list[dict], manual_text: str) -> list[dict]:
    """V2: MANUAL 출처는 매뉴얼 대조, INVARIANT/INFERRED는 skip."""
    failures = []
    normalized = re.sub(r"\s+", " ", manual_text)
    for tc in tcs:
        sq = str(tc.get("source_quote", ""))
        source_type = _classify_source_quote(sq)
        if source_type != "manual":
            continue  # INVARIANT·INFERRED는 V2 대조 대상 아님
        # MANUAL: 접두어 제거 후 대조
        quote = sq.removeprefix("MANUAL:").strip()[:80]
        if len(quote) > 10:
            norm_q = re.sub(r"\s+", " ", quote)
            if norm_q not in normalized:
                failures.append({"tc_id": tc.get("tc_id"), "v": "V2",
                                  "reason": f"source_quote 매뉴얼 불일치: '{quote[:40]}'"})
    return failures


def _v3(tcs: list[dict], threshold: float) -> list[dict]:
    """V3: INFERRED(추론) 비율만 임계 적용. INVARIANT 출처는 신뢰 소스로 분리."""
    if not tcs:
        return []
    inferred_cnt = sum(
        1 for tc in tcs if _classify_source_quote(str(tc.get("source_quote", ""))) == "inferred"
    )
    ratio = inferred_cnt / len(tcs)
    if ratio > threshold:
        return [{"tc_id": "ALL", "v": "V3",
                 "reason": f"INFERRED 비율 {ratio:.1%} > 임계 {threshold:.1%} "
                            f"(INVARIANT 출처는 제외)"}]
    return []


def _v4(tcs: list[dict]) -> list[dict]:
    if not tcs:
        return []
    happy_cnt = sum(1 for tc in tcs if tc.get("design_technique") == "happy_path")
    ratio = happy_cnt / len(tcs)
    if ratio > 0.50:
        return [{"tc_id": "ALL", "v": "V4",
                 "reason": f"happy_path 비율 {ratio:.1%} > 50%"}]
    return []


def _v5(tcs: list[dict], leaves: list[dict]) -> list[dict]:
    covered = {tc.get("requirement_id") for tc in tcs}
    missing = [lf["requirement_id"] for lf in leaves if lf["requirement_id"] not in covered]
    if missing:
        return [{"tc_id": "ALL", "v": "V5",
                 "reason": f"leaf 미커버: {missing}"}]
    return []


def _extract_manual_for_tcs(failed_tcs: list[dict], manual_text: str) -> str:
    """failed_tcs의 소분류(category_leaf) 또는 시나리오 키워드로 매뉴얼 발췌.

    TC가 참조하는 기능명을 키워드로 삼아 매뉴얼에서 관련 단락을 추출한다.
    - 각 TC의 소분류·시나리오에서 첫 단어(핵심 명사) 추출
    - 매뉴얼에서 해당 단어가 포함된 줄 ± 2줄 추출
    - 중복 제거 후 반환
    """
    keywords: set[str] = set()
    for tc in failed_tcs:
        for field in ("소분류", "scenario", "precondition"):
            val = str(tc.get(field, ""))
            # 첫 4 음절어 이상 단어 추출 (공백 분리)
            for word in val.split():
                word = word.strip(".,()[]「」『』")
                if len(word) >= 4:
                    keywords.add(word)
                    if len(keywords) >= 10:
                        break
            if len(keywords) >= 10:
                break

    if not keywords:
        # 키워드 없으면 매뉴얼 앞부분 반환
        return manual_text[:1500]

    lines = manual_text.splitlines()
    hit_lines: list[int] = []
    for i, line in enumerate(lines):
        if any(kw in line for kw in keywords):
            hit_lines.extend(range(max(0, i - 2), min(len(lines), i + 3)))

    if not hit_lines:
        return manual_text[:1500]

    seen: set[int] = set()
    excerpts: list[str] = []
    for idx in sorted(set(hit_lines)):
        if idx not in seen:
            excerpts.append(lines[idx])
            seen.add(idx)

    return "\n".join(excerpts)


def _build_fix_instructions(failures: list[dict]) -> str:
    vs = {f["v"] for f in failures}
    parts = []
    if "V1" in vs:
        parts.append("필수 컬럼을 모두 채우고 tc_id는 TC-XXX-YYY 형식으로 수정하세요.")
    if "V2" in vs:
        parts.append("source_quote는 매뉴얼 원문을 직접 인용하거나 'INFERRED: 근거'로 표기하세요.")
    if "V3" in vs:
        parts.append("INFERRED 비율을 줄이도록 매뉴얼 근거를 더 많이 활용하세요.")
    if "V4" in vs:
        parts.append("happy_path 외 다른 기법(boundary, negative_deep 등)을 더 사용하세요.")
    if "V5" in vs:
        parts.append("모든 leaf 기능에 최소 1개 TC를 포함하세요.")
    if "V10" in vs:
        parts.append(
            "각 leaf의 적용 가능 negative 카테고리(validation_failure/duplicate_or_conflict/"
            "permission_denied/boundary_violation/injection_or_security) 중 누락된 카테고리에 "
            "negative_basic 또는 negative_deep TC를 1개씩 추가하세요."
        )
    return " / ".join(parts)
