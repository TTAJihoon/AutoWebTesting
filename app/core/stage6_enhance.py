"""Stage 6 — 실패 TC 원인 분석 (LLM FAILURE_ANALYSIS 호출)."""
from __future__ import annotations
from typing import Callable


def enhance(
    tcs: list[dict],
    llm_client,
    progress_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """result=fail인 TC에 failure_reason 4축을 채운다."""
    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    failed = [tc for tc in tcs if tc.get("result") == "fail"]
    _cb(f"Stage 6: 실패 TC {len(failed)}개 원인 분석")

    for i, tc in enumerate(failed, 1):
        _cb(f"  분석 중 ({i}/{len(failed)}): {tc['tc_id']}")
        result = llm_client.call("FAILURE_ANALYSIS", {
            "tc_id": tc["tc_id"],
            "scenario": tc.get("scenario", "")[:200],
            "precondition": tc.get("precondition", "")[:300],
            "expected_output": tc.get("expected", "")[:300],
            "actual_output": tc.get("actual", "")[:500],
        })

        parts = [
            f"[실제출력] {result.get('actual_output_summary', '')}",
            f"[차이] {result.get('difference', '')}",
            f"[원인후보] {', '.join(result.get('root_cause_candidates', []))}",
            f"[재시도] {result.get('retry_history', '없음')}",
        ]
        tc["failure_reason"] = "\n".join(parts)
        tc["exec_confidence"] = result.get("exec_confidence", tc.get("exec_confidence", 0.0))

    _cb("Stage 6 완료")
    return tcs
