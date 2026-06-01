"""Stage 0 사전 단계 — URL 목록만 빠르게 BFS 수집 (LLM·스크린샷 X).

페이지 선택 다이얼로그용 데이터를 수집한다.
DOM 분석/스크린샷은 stage0_dom_scan.py에서 별도로 수행.
"""
from __future__ import annotations
from typing import Callable
from playwright.sync_api import sync_playwright


def collect_urls(
    start_url: str,
    max_pages: int = 500,                            # 안전 상한 (사이트 폭발 방지)
    max_depth: int = 2,
    auth_sequence: list[dict] | None = None,
    progress_cb: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,   # 사용자 중단 신호 (협력적)
) -> list[dict]:
    """시작 URL에서 BFS로 같은 origin 페이지를 수집.

    Args:
        max_pages:   안전 상한. 일반적으로 BFS는 자연 종료(같은 origin 링크 소진).
        should_stop: True를 반환하면 BFS 즉시 중단 (협력적 인터럽트).

    Returns:
        [{"url": str, "title": str, "depth": int}, ...]
        — 발견 순서대로. start_url이 첫 항목.
    """
    def _cb(msg: str) -> None:
        if progress_cb:
            progress_cb(msg)

    def _stopped() -> bool:
        return bool(should_stop and should_stop())

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

        # BFS — 시작 URL도 정규화해 끝슬래시/index 차이로 인한 중복 방지
        queue: list[tuple[str, int]] = [(_canonical(start_url) or start_url, 0)]
        stopped_by_user = False
        while queue and len(collected) < max_pages:
            # 사용자 중단 협력 체크
            if _stopped():
                stopped_by_user = True
                _cb("⏹ 사용자 중단 — BFS 종료")
                break

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
                _cb(f"   ({len(collected)}) {title[:40]}  ←  {cur_url}")

                # 같은 origin 링크 수집 (depth + 1)
                if depth < max_depth:
                    links = page.evaluate(
                        "() => [...document.querySelectorAll('a[href]')].map(a=>a.href)"
                    )
                    seen_in_queue = {u for u, _ in queue} | visited
                    for lnk in links:
                        # query string과 fragment 제거 — 동일 페이지의 변형 URL 중복 방지
                        canon = _canonical(lnk)
                        if not canon:
                            continue
                        # 같은 origin & 아직 방문 안 함 & queue에도 없음
                        if (_origin(canon) == base_origin
                                and canon not in seen_in_queue):
                            queue.append((canon, depth + 1))
                            seen_in_queue.add(canon)
            except Exception as e:
                _cb(f"   ⚠ 페이지 스킵 ({cur_url}): {e}")

        browser.close()

    if stopped_by_user:
        _cb(f"URL 수집 중단 — {len(collected)}개까지 수집")
    elif len(collected) >= max_pages:
        _cb(f"URL 수집 한도 도달 ({max_pages}) — {len(collected)}개")
    else:
        _cb(f"URL 수집 완료 — {len(collected)}개 발견 (사이트 BFS 자연 종료)")
    return collected


_INDEX_FILES = ("index.php", "index.html", "index.htm", "default.php", "default.aspx")


def _canonical(url: str) -> str:
    """URL을 정규화해 '같은 페이지의 다른 표기'로 인한 중복을 제거.

    정규화 규칙:
      - fragment(#anchor) 제거 — 같은 페이지의 다른 위치
      - 끝 슬래시 제거 — '/page' 와 '/page/' 동일 취급 (단, 루트는 '/' 유지)
      - index 파일 제거 — '/dir/index.php' → '/dir' (루트는 '/' 유지)
      - query string은 보존 — board.php?bo_table=free 와 ?bo_table=qa 는
        서로 다른 페이지이므로 합치지 않음 (게시판 구분 등)
    """
    from urllib.parse import urlparse, urlunparse
    try:
        u = urlparse(url)
        if not u.scheme or not u.netloc:
            return ""
        path = u.path or "/"
        # index 파일 제거 (query가 없을 때만 — index.php?action=x 는 의미 있을 수 있음)
        if not u.query:
            for idx in _INDEX_FILES:
                if path.lower().endswith("/" + idx):
                    path = path[: -len(idx)]   # '/dir/index.php' → '/dir/'
                    break
        # 끝 슬래시 제거 (루트 제외)
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")
        if not path:
            path = "/"
        return urlunparse((u.scheme, u.netloc, path, u.params, u.query, ""))
    except Exception:
        return url


def _origin(url: str) -> str:
    """URL의 origin(스킴 + 호스트 + 포트) 추출."""
    from urllib.parse import urlparse
    try:
        u = urlparse(url)
        return f"{u.scheme}://{u.netloc}"
    except Exception:
        return ""
