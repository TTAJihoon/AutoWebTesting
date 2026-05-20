"""LLM 호출 래퍼 — provider 추상화 (D48) + stateless 호출 (D38) + 캐시 (D41).

각 Contract의 frontmatter `model:` 필드 prefix에 따라 provider가 자동 선택된다:
    claude-*  → AnthropicProvider
    gpt-*, o1-*, o3-* → OpenAIProvider
    gemini-*  → GeminiProvider

상세: doc/07-llm-providers.md
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path
from typing import Any

from app.api.call_contracts import Contract, load as load_contract
from app.api.providers import provider_name_for_model, resolve_provider, LLMProvider
from app.tools import cache as cache_store

_LOG_DIR = Path("data/runs")


class LLMClient:
    """LLM 호출 진입점. Stage 코드는 이 클래스의 .call()만 사용한다."""

    def __init__(self, api_key: str, run_id: str, provider_override: str | None = None):
        """
        Args:
            api_key: 선택된 provider의 API 키 (UI/.env에서 주입)
            run_id: 실행 ID — 로그 디렉터리 구분
            provider_override: 명시적 provider 이름 (테스트·실험용). 통상은 None — Contract model에서 자동 라우팅
        """
        self._api_key = api_key
        self._run_id = run_id
        self._provider_override = provider_override
        self._log_dir = _LOG_DIR / run_id / "llm"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        # provider 인스턴스 캐시 — 같은 provider는 1회만 생성
        self._providers: dict[str, LLMProvider] = {}

    def _get_provider(self, model: str) -> LLMProvider:
        name = self._provider_override or provider_name_for_model(model)
        if name not in self._providers:
            self._providers[name] = resolve_provider(model, self._api_key)
        return self._providers[name]

    def call(self, contract_id: str, inputs: dict[str, Any], use_cache: bool = True) -> dict:
        """Contract 1회 호출. 캐시 히트 시 API 미호출."""
        contract = load_contract(contract_id)

        # 캐시 키에 model 포함 (다른 모델은 다른 결과 — D48)
        cache_inputs = dict(inputs)
        cache_inputs["__model__"] = contract.model
        if use_cache:
            cached = cache_store.get(contract_id, contract.version, cache_inputs)
            if cached is not None:
                return cached

        user_msg = contract.render_user(**inputs)
        provider = self._get_provider(contract.model)
        start = time.time()

        result_chat = provider.chat(
            system=contract.system_prompt,
            user=user_msg,
            model=contract.model,
            max_tokens=contract.max_output_tokens,
            json_mode=True,
        )

        elapsed = time.time() - start
        result = self._parse_json(result_chat.text)

        self._log(
            contract_id=contract_id,
            provider_name=provider.name,
            inputs=inputs,
            user_msg=user_msg,
            raw=result_chat.text,
            parsed=result,
            elapsed=elapsed,
            input_tokens=result_chat.input_tokens,
            output_tokens=result_chat.output_tokens,
            model=result_chat.model,
        )

        if use_cache:
            cache_store.put(contract_id, contract.version, cache_inputs, result)

        return result

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        # JSON 블록 추출 (```json ... ``` 감싸져 있을 수 있음 — Anthropic 자주 사용)
        if "```" in text:
            m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
            if m:
                text = m.group(1).strip()
        return json.loads(text)

    def _log(
        self,
        contract_id: str,
        provider_name: str,
        inputs: dict,
        user_msg: str,
        raw: str,
        parsed: dict,
        elapsed: float,
        input_tokens: int,
        output_tokens: int,
        model: str,
    ) -> None:
        ts = int(time.time())
        log = {
            "contract_id": contract_id,
            "provider": provider_name,
            "model": model,
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
