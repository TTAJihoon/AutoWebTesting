"""Stage 0 — Playwright DOM 스캔 → LLM 명세 초안 (D32·D33).

변경 이력:
  - DOM elements를 _CHUNK_SIZE(50)개 단위로 분할 → DOM_SPEC 복수 호출로 12000자 제한 해소
  - 페이지별 스크린샷 저장 (dom-scan/screenshots/)
  - 각 feature에 screenshot_file 필드 추가
  - DOM_SPEC 오류 시 최대 3회 재시도; 전체 features=0이면 RuntimeError 발생
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Callable

from playwright.sync_api import sync_playwright, Page

_ALLOWED_ATTRS   = {"id", "name", "type", "placeholder", "aria-label", "href"}
_INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea", "form", "label"}

# 청크 1개당 DOM 요소 수 — 50개 × ~100자 ≈ 5,000자 → max_input_tokens(8,000)에 여유 있게 맞춤
_CHUNK_SIZE       = 50
# DOM_SPEC 오류 시 청크별 최대 재시도 횟수
_CHUNK_MAX_RETRY  = 3


def _extract_elements(page: Page) -> list[dict]:
    return page.evaluate("""() => {
        const tags = ['a','button','input','select','textarea','form','label','h1','h2','h3','nav'];
        const results = [];
        for (const tag of tags) {
            for (const el of document.querySelectorAll(tag)) {
                const obj = {tag};
                const keep = ['id','name','type','placeholder','aria-label','href'];
                for (const attr of keep) {
                    const v = el.getAttribute(attr);
                    if (v) obj[attr] = v.substring(0, 100);
                }
                const text = el.innerText?.trim().substring(0, 80);
                if (text) obj.text = text;
                results.push(obj);
            }
        }
        return results;
    }""")


def _chunk_elements(elements: list[dict], chunk_size: int = _CHUNK_SIZE) -> list[list[dict]]:
    """DOM 요소 목록을 chunk_size 단위 배치로 분할."""
    return [elements[i : i + chunk_size] for i in range(0, max(len(elements), 1), chunk_size)]


def _safe_filename(url: str, base_url: str) -> str:
    """URL 경로를 파일명용 안전 문자열로 변환 (최대 40자)."""
    path = url.replace(base_url, "").strip("/") or "home"
    return re.sub(r"[^\w\-]", "_", path)[:40]


def scan(
    url: str,
    llm_client,
    run_dir: Path,
    auth_sequence: list[dict] | None = None,
    max_pages: int = 30,
    progress_cb: Callable[[str], None] | None = None,
    selected_urls: list[str] | None = None,
    cached_features: dict[str, list[dict]] | None = None,
) -> dict:
    """URL을 스캔해 feature-spec-draft.md 생성. LLM 명세 초안 반환.

    Args:
        url:             시작 URL (BFS 기준)
        max_pages:       BFS 최대 페이지 수 (selected_urls가 있으면 무시)
        selected_urls:   None이면 기존 BFS 방식. 리스트면 그 URL만 처리(BFS 생략).
        cached_features: {url: [features...]} — 이 URL은 LLM 호출 생략, 캐시 features 그대로 사용.

    Raises:
        RuntimeError: 모든 페이지 스캔 후 features가 0개인 경우
                      (LLM API 오류·키 오류 등 원인 가능성 높음)
    """
    out_dir = run_dir / "dom-scan"
    out_dir.mkdir(parents=True, exist_ok=True)

    screenshots_dir = out_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    all_features: list[dict] = []
    visited: set[str] = set()
    llm_error_count = 0          # LLM 호출 실패 누적
    llm_call_count  = 0          # LLM 호출 성공 누적
    cache_hit_count = 0          # 캐시 재사용 페이지 수

    cached_features = cached_features or {}

    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page    = context.new_page()

        _cb(f"접속 중: {url}")
        page.goto(url, wait_until="networkidle", timeout=30000)

        # 인증 시퀀스 (D33 — 하드코딩 금지, 실행 시점 입력)
        if auth_sequence:
            for step in auth_sequence:
                action = step.get("action")
                if action == "fill":
                    page.fill(step["selector"], step["value"])
                elif action == "click":
                    page.click(step["selector"])
                    page.wait_for_load_state("networkidle", timeout=10000)
            _cb("인증 완료")

        # ── 페이지 큐 결정 ────────────────────────────────────────────────────
        # selected_urls가 주어지면 그것만 처리(BFS 생략), 아니면 기존 BFS
        if selected_urls is not None:
            queue: list[tuple[str, int]] = [(u, 0) for u in selected_urls]
            do_bfs = False
            total_pages = len(selected_urls)
        else:
            queue = [(url, 0)]
            do_bfs = True
            total_pages = max_pages

        while queue and len(visited) < total_pages:
            cur_url, depth = queue.pop(0)
            if cur_url in visited:
                continue
            visited.add(cur_url)

            # ── 캐시 hit: LLM 호출 생략 ────────────────────────────────────
            if cur_url in cached_features:
                cached = cached_features[cur_url]
                # 캐시된 feature를 그대로 추가 (source_url 보존)
                for feat in cached:
                    f = dict(feat)
                    f.setdefault("source_url", cur_url)
                    all_features.append(f)
                cache_hit_count += 1
                page_idx = len(visited)
                _cb(
                    f"♻ 캐시 재사용 ({page_idx}/{total_pages}): "
                    f"{cur_url} — 기능 {len(cached)}개"
                )
                continue

            try:
                if cur_url != page.url:
                    page.goto(cur_url, wait_until="networkidle", timeout=20000)

                page_idx = len(visited)
                _cb(f"스캔 중 ({page_idx}/{total_pages}): {cur_url}")

                # ── 스크린샷 저장 ────────────────────────────────────────────
                screenshot_name = f"page_{page_idx:03d}_{_safe_filename(cur_url, url)}.png"
                try:
                    page.screenshot(
                        path=str(screenshots_dir / screenshot_name),
                        full_page=True,
                    )
                    _cb(f"  스크린샷 저장: {screenshot_name}")
                except Exception as ss_err:
                    _cb(f"  스크린샷 실패 (무시): {ss_err}")
                    screenshot_name = ""

                # ── DOM 요소 추출 ────────────────────────────────────────────
                elements = _extract_elements(page)
                if not elements:
                    _cb(f"  DOM 요소 없음 — 스킵: {cur_url}")
                    continue

                chunks = _chunk_elements(elements)
                _cb(f"  DOM 요소 {len(elements)}개 → {len(chunks)}개 청크로 분할")

                # ── 청크별 DOM_SPEC 호출 (오류 시 재시도) ────────────────────
                page_feature_count = 0
                for chunk_idx, chunk in enumerate(chunks, 1):
                    success = False
                    for attempt in range(1, _CHUNK_MAX_RETRY + 1):
                        try:
                            result = llm_client.call("DOM_SPEC", {
                                "url": cur_url,
                                "dom_elements_json": json.dumps(
                                    chunk, ensure_ascii=False
                                ),
                            })
                            llm_call_count += 1
                            feats = result.get("features", [])
                            for feat in feats:
                                feat["screenshot_file"] = screenshot_name
                                feat["source_url"]      = cur_url   # URL별 캐시용
                            all_features.extend(feats)
                            page_feature_count += len(feats)
                            if not feats:
                                _cb(f"  청크 {chunk_idx}/{len(chunks)}: features 0개 "
                                    f"(요소 미흡 가능)")
                            success = True
                            break
                        except Exception as e:
                            llm_error_count += 1
                            if attempt < _CHUNK_MAX_RETRY:
                                _cb(f"  ⚠ DOM_SPEC 오류 재시도 "
                                    f"({attempt}/{_CHUNK_MAX_RETRY}): {e}")
                            else:
                                _cb(f"  ✗ DOM_SPEC 최종 실패 "
                                    f"(청크 {chunk_idx}/{len(chunks)}): {e}")

                    if not success:
                        _cb(f"  청크 {chunk_idx} 건너뜀")

                _cb(f"  페이지 기능 {page_feature_count}개 추출")

                # 같은 origin 링크 수집 (depth+1) — selected_urls 모드에서는 생략
                if do_bfs and depth < 2:
                    links = page.evaluate(
                        "() => [...document.querySelectorAll('a[href]')].map(a=>a.href)"
                    )
                    for lnk in links:
                        if lnk.startswith(url) and lnk not in visited:
                            queue.append((lnk, depth + 1))

            except Exception as e:
                _cb(f"  페이지 스킵 ({cur_url}): {e}")

        browser.close()

    # ── 명세 초안 저장 ────────────────────────────────────────────────────────
    draft = {
        "url":           url,
        "pages_scanned": len(visited),
        "features":      all_features,
        "llm_calls":     llm_call_count,
        "llm_errors":    llm_error_count,
        "cache_hits":    cache_hit_count,
    }
    spec_path = out_dir / "feature-spec-draft.json"
    spec_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")

    # 마크다운도 생성
    md_lines = [
        f"# 기능 명세 초안\n\n"
        f"> URL: {url}  |  스캔 페이지: {len(visited)}  |  기능 추출: {len(all_features)}개\n"
    ]
    for f in all_features:
        md_lines.append(
            f"## {f['category_major']} > {f['category_mid']} > {f['category_leaf']}\n"
            f"- 명세: {f.get('implicit_spec','')}\n"
            f"- 근거 요소: `{f.get('source_element','')}`  신뢰도: {f.get('confidence','')}\n"
            f"- 스크린샷: {f.get('screenshot_file','')}\n"
        )
    (out_dir / "feature-spec-draft.md").write_text("\n".join(md_lines), encoding="utf-8")

    _cb(f"Stage 0 완료 - 기능 {len(all_features)}개 추출 "
        f"(LLM 호출 {llm_call_count}회, 오류 {llm_error_count}회)")

    # ── features 0개 → 진행 불가 ─────────────────────────────────────────────
    if not all_features:
        err_parts = [
            "Stage 0: 기능 목록이 0개입니다. Stage 1로 진행할 수 없습니다.",
            "",
            f"  - 스캔 페이지: {len(visited)}개",
            f"  - LLM 호출 시도: {llm_call_count}회 성공 / {llm_error_count}회 실패",
            "",
            "가능한 원인:",
        ]
        if llm_error_count > 0 and llm_call_count == 0:
            err_parts += [
                "  [LLM API 오류] API 키가 잘못됐거나 네트워크가 LLM 서버를 차단 중입니다.",
                "  → 대시보드 설정 탭에서 API 키를 확인하세요.",
            ]
        elif llm_call_count > 0:
            err_parts += [
                "  [LLM 응답 미흡] LLM이 기능을 추출하지 못했습니다.",
                "  → 대상 페이지의 DOM 구조가 너무 단순하거나 로그인 등 인증이 필요할 수 있습니다.",
            ]
        else:
            err_parts += [
                "  [DOM 요소 없음] 스캔된 모든 페이지에서 인터랙티브 요소를 찾지 못했습니다.",
            ]
        raise RuntimeError("\n".join(err_parts))

    return draft
