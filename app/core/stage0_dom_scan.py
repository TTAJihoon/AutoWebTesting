"""Stage 0 — Playwright DOM 스캔 → LLM 명세 초안 (D32·D33)."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Callable

from playwright.sync_api import sync_playwright, Page

_ALLOWED_ATTRS = {"id", "name", "type", "placeholder", "aria-label", "href"}
_INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea", "form", "label"}


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


def scan(
    url: str,
    llm_client,
    run_dir: Path,
    auth_sequence: list[dict] | None = None,
    max_pages: int = 30,
    progress_cb: Callable[[str], None] | None = None,
) -> dict:
    """URL을 스캔해 feature-spec-draft.md 생성. LLM 명세 초안 반환."""
    out_dir = run_dir / "dom-scan"
    out_dir.mkdir(parents=True, exist_ok=True)

    all_features: list[dict] = []
    visited: set[str] = set()

    def _cb(msg: str):
        if progress_cb:
            progress_cb(msg)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

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

        # BFS 페이지 수집 (depth ≤ 2)
        queue = [(url, 0)]
        while queue and len(visited) < max_pages:
            cur_url, depth = queue.pop(0)
            if cur_url in visited:
                continue
            visited.add(cur_url)

            try:
                if cur_url != page.url:
                    page.goto(cur_url, wait_until="networkidle", timeout=20000)
                _cb(f"스캔 중 ({len(visited)}/{max_pages}): {cur_url}")
                elements = _extract_elements(page)

                # DOM_SPEC LLM 호출
                result = llm_client.call("DOM_SPEC", {
                    "url": cur_url,
                    "dom_elements_json": json.dumps(elements, ensure_ascii=False)[:12000],
                })
                all_features.extend(result.get("features", []))

                # 같은 origin 링크 수집 (depth+1)
                if depth < 2:
                    links = page.evaluate(
                        "() => [...document.querySelectorAll('a[href]')].map(a=>a.href)"
                    )
                    for lnk in links:
                        if lnk.startswith(url) and lnk not in visited:
                            queue.append((lnk, depth + 1))

            except Exception as e:
                _cb(f"  스킵 ({cur_url}): {e}")

        browser.close()

    # 명세 초안 저장
    draft = {"url": url, "pages_scanned": len(visited), "features": all_features}
    spec_path = out_dir / "feature-spec-draft.json"
    spec_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")

    # 마크다운도 생성
    md_lines = [f"# 기능 명세 초안\n\n> URL: {url}  |  스캔 페이지: {len(visited)}\n"]
    for f in all_features:
        md_lines.append(
            f"## {f['category_major']} > {f['category_mid']} > {f['category_leaf']}\n"
            f"- 명세: {f.get('implicit_spec','')}\n"
            f"- 근거 요소: `{f.get('source_element','')}`  신뢰도: {f.get('confidence','')}\n"
        )
    (out_dir / "feature-spec-draft.md").write_text("\n".join(md_lines), encoding="utf-8")

    _cb(f"Stage 0 완료 - 기능 {len(all_features)}개 추출")
    return draft
