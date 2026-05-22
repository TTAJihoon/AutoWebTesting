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

    # 모델별 최소 호출 간격(초) — free tier RPM 기반
    _MIN_INTERVAL: dict[str, float] = {
        "gemini-3.5-flash":      13.0,  # 5 RPM → 60/5 = 12s + 1s 여유
        "gemini-3.1-flash-lite":  6.0,  # 10 RPM → 60/10 = 6s
        "gemini-2.5-flash":      13.0,
        "gemini-2.5-flash-lite":  6.0,
        "gemini-2.0-flash":       6.0,
        "gemini-2.0-flash-lite":  6.0,
        "gemini-1.5-flash":       5.0,
        "gemma-4-26b-a4b-it":   12.0,   # Gemma 4 26B (preview — 500 오류 방지용 보수적 간격)
        "gemma-4-31b-it":       12.0,   # Gemma 4 31B
    }

    def __init__(
        self,
        api_key: str,
        run_id: str,
        provider_override: str | None = None,
        model_override: str | None = None,
        progress_cb: Any = None,
    ):
        """
        Args:
            api_key: 선택된 provider의 API 키 (UI/.env에서 주입)
            run_id: 실행 ID — 로그 디렉터리 구분
            provider_override: 명시적 provider 이름 (테스트·실험용). 통상은 None — Contract model에서 자동 라우팅
            model_override: Contract frontmatter의 model을 이 값으로 교체.
                예) "gemini-3.5-flash" 설정 시 모든 Contract가 Gemini로 실행됨.
                None이면 각 Contract의 model을 그대로 사용.
            progress_cb: 재시도 메시지를 GUI 로그로 전달하기 위한 콜백 (선택)
        """
        self._api_key = api_key
        self._run_id = run_id
        self._provider_override = provider_override
        self._model_override = model_override
        self._progress_cb = progress_cb
        self._log_dir = _LOG_DIR / run_id / "llm"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        # provider 인스턴스 캐시 — 같은 provider는 1회만 생성
        self._providers: dict[str, LLMProvider] = {}
        # RPM 제어 — 마지막 실제 API 호출 시각
        self._last_call_time: float = 0.0

    def _get_provider(self, model: str) -> LLMProvider:
        name = self._provider_override or provider_name_for_model(model)
        if name not in self._providers:
            self._providers[name] = resolve_provider(model, self._api_key)
        return self._providers[name]

    def call(
        self,
        contract_id: str,
        inputs: dict[str, Any],
        use_cache: bool = True,
        _retry_count: int = 0,
    ) -> dict:
        """Contract 1회 호출. 캐시 히트 시 API 미호출.

        503/429 일시 오류는 최대 3회 지수 백오프 재시도.
        """
        contract = load_contract(contract_id)
        # model_override가 있으면 Contract 모델 대신 사용 (다른 provider 전환 시)
        effective_model = self._model_override or contract.model

        # 캐시 키에 model 포함 (다른 모델은 다른 결과 — D48)
        cache_inputs = dict(inputs)
        cache_inputs["__model__"] = effective_model
        if use_cache:
            cached = cache_store.get(contract_id, contract.version, cache_inputs)
            if cached is not None:
                return cached

        user_msg = contract.render_user(**inputs)
        provider = self._get_provider(effective_model)

        # RPM 스로틀링 — 모델별 최소 간격 적용 (캐시 히트는 제외됨)
        min_interval = self._MIN_INTERVAL.get(effective_model, 0.0)
        if min_interval > 0 and _retry_count == 0:
            elapsed_since_last = time.time() - self._last_call_time
            if elapsed_since_last < min_interval:
                wait = min_interval - elapsed_since_last
                time.sleep(wait)

        start = time.time()
        self._last_call_time = start

        try:
            result_chat = provider.chat(
                system=contract.system_prompt,
                user=user_msg,
                model=effective_model,
                max_tokens=contract.max_output_tokens,
                json_mode=True,
            )
        except Exception as e:
            # 일시적 서버/속도 오류 — 최대 5회 지수 백오프 재시도
            # 500 INTERNAL: Gemini 서버 과부하 (일시적)
            # 503 UNAVAILABLE / 429 RESOURCE_EXHAUSTED: 속도 제한
            err_str = str(e)
            if _retry_count < 5 and any(
                code in err_str for code in (
                    "500", "503", "429",
                    "INTERNAL", "UNAVAILABLE", "RESOURCE_EXHAUSTED",
                )
            ):
                wait_sec = 15 * (2 ** _retry_count)  # 15 → 30 → 60 → 120 → 240초
                try:
                    self._log_retry(contract_id, _retry_count + 1, wait_sec, err_str)
                except Exception:
                    pass  # 로그 실패가 재시도를 막지 않도록
                time.sleep(wait_sec)
                return self.call(contract_id, inputs, use_cache, _retry_count + 1)
            raise

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

    def _log_retry(self, contract_id: str, attempt: int, wait_sec: int, err: str) -> None:
        import sys
        # 오류 메시지에서 핵심 상태 코드만 추출 (긴 traceback 제거)
        err_summary = err.splitlines()[0][:100] if err else ""
        msg = (
            f"  [재시도 {attempt}/5] {contract_id} - {wait_sec}초 대기 중... "
            f"({err_summary})"
        )
        # GUI progress_cb 우선 사용 (없으면 stderr fallback)
        if self._progress_cb:
            try:
                self._progress_cb(msg)
            except Exception:
                pass
        else:
            try:
                print(msg, file=sys.stderr)
            except (UnicodeEncodeError, OSError):
                safe = msg.encode("ascii", errors="replace").decode("ascii")
                try:
                    print(safe, file=sys.stderr)
                except Exception:
                    pass

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        # JSON 블록 추출 (```json ... ``` 감싸져 있을 수 있음 — Anthropic 자주 사용)
        if "```" in text:
            m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
            if m:
                text = m.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # "Extra data" — 첫 번째 완성된 JSON 객체만 추출 (Gemini 재시도 시 간헐 발생)
            if "Extra data" in str(e):
                decoder = json.JSONDecoder()
                obj, _ = decoder.raw_decode(text)
                if isinstance(obj, dict):
                    return obj
            raise

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
