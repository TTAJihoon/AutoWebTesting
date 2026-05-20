"""Google Gemini provider 구현 (google-genai 신 SDK 기준)."""
from __future__ import annotations

from app.api.providers.base import ChatResult, LLMProvider


class GeminiProvider(LLMProvider):
    name = "google"

    def __init__(self, api_key: str):
        try:
            from google import genai
        except ImportError as e:
            raise RuntimeError(
                "Gemini provider requires 'google-genai' package. "
                "Install: pip install google-genai>=0.3.0"
            ) from e
        if not api_key:
            raise ValueError("Google API key is empty.")
        self._genai = genai
        self._client = genai.Client(api_key=api_key)

    def chat(
        self,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
        json_mode: bool = True,
    ) -> ChatResult:
        from google.genai import types

        config_kwargs: dict = {
            "max_output_tokens": max_tokens,
            "system_instruction": system,
        }
        if json_mode:
            config_kwargs["response_mime_type"] = "application/json"

        # Gemini 2.5 Flash/Pro 는 thinking 기능이 기본 ON.
        # thinking 토큰이 max_output_tokens 예산을 잠식해 JSON이 중간에 잘리는 문제를 방지.
        # JSON 출력 용도에서는 thinking을 비활성화해 예산 전체를 실제 응답에 사용.
        try:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        except (AttributeError, TypeError):
            pass  # SDK가 ThinkingConfig 미지원 시 무시

        response = self._client.models.generate_content(
            model=model,
            contents=user,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        text = response.text or ""
        # Gemini usage_metadata: prompt_token_count, candidates_token_count
        usage = response.usage_metadata
        input_tokens = getattr(usage, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage, "candidates_token_count", 0) or 0

        return ChatResult(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            raw=None,  # google-genai 응답은 dict 변환 까다로움 — 디버그는 별도 처리
        )
