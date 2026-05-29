"""Stage 0 사전 단계 — URL 목록만 빠르게 BFS 수집 (LLM·스크린샷 X).

페이지 선택 다이얼로그용 데이터를 수집한다.
DOM 분석/스크린샷은 stage0_dom_scan.py에서 별도로 수행.
"""
from __future__ import annotations
from typing import Callable
from playwright.sync_api import sync_playwright


def collect_urls(
    start_url: str,
    max_pages: int = 30,
    max_depth: int = 2,
    auth_sequence: list[dict] | None = None,
    progress_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """시작 URL에서 BFS로 같은 origin 페이지를 수집.

    Returns:
        [{"url": str, "title": str, "depth": int}, ...]
        — 발견 순서대로. start_url이 첫 항목.
    """
    def _cb(msg: str) -> None:
        if progress_cb:
            progress_cb(msg)

    collected: list[dict] = []
    visited: set[str] = set()
    base_origin = _origin(start_url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page    = context.new_page()

        _cb(f"URL 수집 시작: {start_url}")
        try:
            page.goto(start_url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            _cb(f"⚠ 시작 URL 접근 실패: {e}")
            browser.close()
            return collected

        # 인증 시퀀스 (필요 시)
        if auth_sequence:
            for step in auth_sequence:
                action = step.get("action")
                try:
                    if action == "fill":
                        page.fill(step["selector"], step["value"])
                    elif action == "click":
                        page.click(step["selector"])
                        page.wait_for_load_state("networkidle", timeout=10000)
                    elif action == "goto":
                        page.goto(step.get("url", step.get("selector", "")),
                                  wait_until="networkidle", timeout=20000)
                except Exception as e:
                    _cb(f"⚠ 인증 단계 실패 (무시): {e}")
            _cb("인증 완료")

        # BFS
        queue: list[tuple[str, int]] = [(start_url, 0)]
        while queue and len(collected) < max_pages:
            cur_url, depth = queue.pop(0)
            if cur_url in visited:
                continue
            visited.add(cur_url)

            try:
                if cur_url != page.url:
                    page.goto(cur_url, wait_until="networkidle", timeout=20000)

                title = (page.title() or "").strip() or "(제목 없음)"
                collected.append({
                    "url":   cur_url,
                    "title": title[:80],
                    "depth": depth,
                })
                _cb(f"   ({len(collected)}/{max_pages}) {title[:40]}  ←  {cur_url}")

                # 같은 origin 링크 수집 (depth + 1)
                if depth < max_depth:
                    links = page.evaluate(
                        "() => [...document.querySelectorAll('a[href]')].map(a=>a.href)"
                    )
                    seen_in_queue = {u for u, _ in queue} | visited
                    for lnk in links:
                        # 같은 origin & 아직 방문 안 함 & queue에도 없음
                        if (_origin(lnk) == base_origin
                                and lnk not in seen_in_queue
                                and "#" not in lnk):   # 앵커 링크 제외
                            queue.append((lnk, depth + 1))
                            seen_in_queue.add(lnk)
            except Exception as e:
                _cb(f"   ⚠ 페이지 스킵 ({cur_url}): {e}")

        browser.close()

    _cb(f"URL 수집 완료 — {len(collected)}개 발견")
    return collected


def _origin(url: str) -> str:
    """URL의 origin(스킴 + 호스트 + 포트) 추출."""
    from urllib.parse import urlparse
    try:
        u = urlparse(url)
        return f"{u.scheme}://{u.netloc}"
    except Exception:
        return ""
