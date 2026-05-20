"""OpenAI GPT provider 구현."""
from __future__ import annotations

from app.api.providers.base import ChatResult, LLMProvider


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError(
                "OpenAI provider requires 'openai' package. "
                "Install: pip install openai>=1.50.0"
            ) from e
        if not api_key:
            raise ValueError("OpenAI API key is empty.")
        self._OpenAI = OpenAI
        self._client = OpenAI(api_key=api_key)

    def chat(
        self,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
        json_mode: bool = True,
    ) -> ChatResult:
        # OpenAI: native JSON mode 사용 (response_format)
        # 단, json_mode 사용 시 system 또는 user 메시지에 "json" 단어가 포함되어야 함 (API 요구사항)
        if json_mode:
            if "json" not in (system + user).lower():
                system = system + "\n\nReturn the response as a JSON object."

        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        text = choice.message.content or ""
        return ChatResult(
            text=text,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=response.model,
            raw=response.model_dump() if hasattr(response, "model_dump") else None,
        )
