"""Anthropic API 래퍼 — stateless 호출 + 캐시 + LLM 로그 (D38·D41)."""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any

import anthropic

from app.api.call_contracts import Contract, load as load_contract
from app.tools import cache as cache_store

_LOG_DIR = Path("data/runs")


class LLMClient:
    def __init__(self, api_key: str, run_id: str):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._run_id = run_id
        self._log_dir = _LOG_DIR / run_id / "llm"
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def call(self, contract_id: str, inputs: dict[str, Any], use_cache: bool = True) -> dict:
        """Contract 1회 호출. 캐시 히트 시 API 미호출."""
        contract = load_contract(contract_id)

        if use_cache:
            cached = cache_store.get(contract_id, contract.version, inputs)
            if cached is not None:
                return cached

        user_msg = contract.render_user(**inputs)
        start = time.time()

        response = self._client.messages.create(
            model=contract.model,
            max_tokens=contract.max_output_tokens,
            system=contract.system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )

        elapsed = time.time() - start
        raw_text = response.content[0].text
        result = self._parse_json(raw_text)

        self._log(contract_id, inputs, user_msg, raw_text, result, elapsed,
                  response.usage.input_tokens, response.usage.output_tokens)

        if use_cache:
            cache_store.put(contract_id, contract.version, inputs, result)

        return result

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        # JSON 블록 추출 (```json ... ``` 감싸져 있을 수 있음)
        if "```" in text:
            import re
            m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
            if m:
                text = m.group(1).strip()
        return json.loads(text)

    def _log(self, contract_id: str, inputs: dict, user_msg: str,
             raw: str, parsed: dict, elapsed: float,
             input_tokens: int, output_tokens: int) -> None:
        ts = int(time.time())
        log = {
            "contract_id": contract_id,
            "timestamp": ts,
            "elapsed_sec": round(elapsed, 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "inputs": inputs,
            "user_message": user_msg,
            "raw_response": raw,
            "parsed": parsed,
        }
        log_path = self._log_dir / f"{ts}_{contract_id}.json"
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
