"""Stage 5 — Playwright TC 자동 실행 (D39)."""
from __future__ import annotations
import time
from typing import Callable

from playwright.sync_api import sync_playwright, Page, expect
from app.validation.v6_selector_stability import annotate as v6_annotate, format_report as v6_format


def execute(
    tcs: list[dict],
    base_url: str,
    auth_sequence: list[dict] | None = None,
    progress_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """approved/edited TC를 Playwright로 실행. result/actual/exec_confidence 채움."""
    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    runnable = [tc for tc in tcs if tc.get("review_status") in ("approved", "edited")]
    _cb(f"Stage 5: {len(runnable)}개 TC 자동 실행 시작")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(base_url, wait_until="networkidle", timeout=30000)
        if auth_sequence:
            _run_auth(page, auth_sequence)

        for i, tc in enumerate(runnable, 1):
            _cb(f"  실행 중 ({i}/{len(runnable)}): {tc['tc_id']}")
            _run_tc(page, tc, base_url)

        browser.close()

    not_run = [tc for tc in tcs if tc.get("review_status") not in ("approved", "edited")]
    for tc in not_run:
        tc["result"] = "not_executed"

    # V6: 선택자 안정성 점수 + 실패 분류 보정
    tcs, v6_report = v6_annotate(tcs, overwrite_exec_confidence=True)
    _cb(v6_format(v6_report))

    _cb(f"Stage 5 완료")
    return tcs


def _run_auth(page: Page, auth_sequence: list[dict]) -> None:
    for step in auth_sequence:
        action = step.get("action")
        if action == "goto":
            page.goto(step["url"], wait_until="networkidle")
        elif action == "fill":
            page.fill(step["selector"], step["value"])
        elif action == "click":
            page.click(step["selector"])
            page.wait_for_load_state("networkidle", timeout=10000)


def _run_tc(page: Page, tc: dict, base_url: str) -> None:
    start = time.time()
    try:
        # precondition에서 액션 파싱 (자연어 → 간단한 패턴 매칭)
        _apply_precondition(page, tc.get("precondition", ""), base_url)

        # 기대 출력 검증
        expected = tc.get("expected", "")
        actual_text = page.content()[:2000]

        if expected and any(kw in actual_text for kw in _key_phrases(expected)):
            tc["result"] = "pass"
            tc["actual"] = f"기대 패턴 확인: {expected[:100]}"
        else:
            tc["result"] = "fail"
            tc["actual"] = f"페이지 내용 일부: {actual_text[:300]}"

        elapsed = time.time() - start
        tc["exec_confidence"] = min(1.0, round(0.9 - elapsed * 0.01, 2))

    except Exception as e:
        tc["result"] = "blocked"
        tc["actual"] = f"실행 오류: {str(e)[:200]}"
        tc["exec_confidence"] = 0.1


def _apply_precondition(page: Page, precondition: str, base_url: str) -> None:
    """precondition 자연어에서 기본 액션 추출 (간단한 휴리스틱)."""
    lower = precondition.lower()
    if "로그인" in lower and "비로그인" not in lower:
        # 이미 로그인 상태인지 확인
        if "로그아웃" not in page.content():
            page.goto(base_url, wait_until="networkidle", timeout=15000)
    elif "비로그인" in lower:
        page.goto(base_url, wait_until="networkidle", timeout=15000)
    else:
        page.goto(base_url, wait_until="networkidle", timeout=15000)


def _key_phrases(expected: str) -> list[str]:
    """기대 출력에서 검증 키워드 추출."""
    import re
    quoted = re.findall(r"[`'\"](.+?)[`'\"]", expected)
    if quoted:
        return quoted
    words = [w for w in expected.split() if len(w) > 3]
    return words[:5] if words else [expected[:30]]
