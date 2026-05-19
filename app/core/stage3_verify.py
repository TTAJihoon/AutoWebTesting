"""Stage 3 — V1~V5 검증 + 실패 시 TC_REGEN 재호출 (doc/03-tc-schema.md §5)."""
from __future__ import annotations
import re
from typing import Callable

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
        failures = _check_all(tcs, manual_text, leaves, inferred_threshold)
        if not failures:
            _cb(f"Stage 3 완료 (시도 {attempt}회) — 모든 검증 통과")
            return tcs

        _cb(f"  V 실패 {len(failures)}건 (시도 {attempt}/{max_retries}) — TC_REGEN 호출")
        failed_ids = {f["tc_id"] for f in failures}
        failed_tcs = [tc for tc in tcs if tc.get("tc_id") in failed_ids]

        fix_instructions = _build_fix_instructions(failures)
        regen_result = llm_client.call("TC_REGEN", {
            "failed_tcs_json": str(failed_tcs)[:3000],
            "v_failures": str(failures)[:600],
            "fix_instructions": fix_instructions[:400],
        })

        # 재생성된 TC로 교체
        regen_map = {tc["tc_id"]: tc for tc in regen_result.get("tcs", [])}
        for i, tc in enumerate(tcs):
            if tc.get("tc_id") in regen_map:
                tcs[i] = {**tc, **regen_map[tc["tc_id"]]}

    # 최대 재시도 초과 — INFERRED 마킹
    _cb("Stage 3: 최대 재시도 초과 — 잔여 실패 TC를 INFERRED 마킹")
    remaining = _check_all(tcs, manual_text, leaves, inferred_threshold)
    failed_ids = {f["tc_id"] for f in remaining}
    for tc in tcs:
        if tc.get("tc_id") in failed_ids:
            tc["source_quote"] = "INFERRED: max_retry_exceeded"
            tc["review_status"] = "pending"
    return tcs


def _check_all(tcs, manual_text, leaves, inferred_threshold) -> list[dict]:
    failures = []
    failures += _v1(tcs)
    failures += _v2(tcs, manual_text)
    failures += _v3(tcs, inferred_threshold)
    failures += _v4(tcs)
    failures += _v5(tcs, leaves)
    return failures


def _v1(tcs: list[dict]) -> list[dict]:
    failures = []
    for tc in tcs:
        missing = [c for c in _REQUIRED_COLS if not str(tc.get(c, "")).strip()]
        if missing or not _TC_ID_RE.match(str(tc.get("tc_id", ""))):
            failures.append({"tc_id": tc.get("tc_id", "?"), "v": "V1",
                              "reason": f"필수 컬럼 비어있거나 tc_id 형식 오류: {missing}"})
    return failures


def _v2(tcs: list[dict], manual_text: str) -> list[dict]:
    failures = []
    normalized = re.sub(r"\s+", " ", manual_text)
    for tc in tcs:
        sq = str(tc.get("source_quote", ""))
        if sq.startswith("INFERRED"):
            continue
        # 30자 이상 인용문은 매뉴얼에서 검색
        quote = sq[:80].strip()
        if len(quote) > 10:
            norm_q = re.sub(r"\s+", " ", quote)
            if norm_q not in normalized:
                failures.append({"tc_id": tc.get("tc_id"), "v": "V2",
                                  "reason": f"source_quote 매뉴얼 불일치: '{quote[:40]}'"})
    return failures


def _v3(tcs: list[dict], threshold: float) -> list[dict]:
    if not tcs:
        return []
    inferred_cnt = sum(
        1 for tc in tcs if str(tc.get("source_quote", "")).startswith("INFERRED")
    )
    ratio = inferred_cnt / len(tcs)
    if ratio > threshold:
        return [{"tc_id": "ALL", "v": "V3",
                 "reason": f"INFERRED 비율 {ratio:.1%} > 임계 {threshold:.1%}"}]
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
    return " / ".join(parts)
