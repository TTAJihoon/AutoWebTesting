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

        m = model.lower()
        # gemma-* 제외, gemini-* 계열은 버전 무관 모두 thinking 비활성화 대상
        _is_gemini = m.startswith("gemini-")
        _is_gemma  = m.startswith("gemma-")

        config_kwargs: dict = {"max_output_tokens": max_tokens}

        # system_instruction: gemma-* 모델은 미지원 → user 프롬프트에 병합
        if _is_gemma:
            contents = f"{system}\n\n---\n\n{user}" if system else user
        else:
            config_kwargs["system_instruction"] = system
            contents = user

        # JSON 모드: gemma-* 미지원 → 프롬프트에 JSON 요청 추가
        if json_mode and not _is_gemma:
            config_kwargs["response_mime_type"] = "application/json"
        elif json_mode and _is_gemma:
            contents += "\n\n반드시 JSON만 출력하고 다른 텍스트는 포함하지 마세요."

        # thinking_budget=0: gemini-* 전 계열 (2.x / 3.x 포함)
        # thinking 토큰이 max_output_tokens 예산을 잠식해 JSON 중간 절단되는 문제 방지
        if _is_gemini:
            try:
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
            except (AttributeError, TypeError):
                pass

        response = self._client.models.generate_content(
            model=model,
            contents=contents,
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
