"""API 키 + 활성 provider Fernet 암호화 저장/로드 (D42, D48).

저장 데이터 구조:
    {
        "active_provider": "anthropic" | "openai" | "google",
        "anthropic_key": "...",
        "openai_key": "...",
        "google_key": "..."
    }

기존 단일 키 형태 {"api_key": "..."}는 자동 마이그레이션 (anthropic_key로 이동).
"""
import os
import json
import hashlib
import platform
from pathlib import Path
from cryptography.fernet import Fernet

try:
    import sys
    from dotenv import load_dotenv
    if getattr(sys, "frozen", False):
        _env_path = Path(sys.executable).parent / ".env"
    else:
        _env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass

_CONFIG_DIR = Path.home() / ".awt"
_CONFIG_FILE = _CONFIG_DIR / "settings.enc"

VALID_PROVIDERS = ("anthropic", "openai", "google")
_DEFAULT_PROVIDER = "anthropic"

# provider 이름 → 저장 키
_KEY_FIELD = {
    "anthropic": "anthropic_key",
    "openai": "openai_key",
    "google": "google_key",
}


def _machine_key() -> bytes:
    """머신 고유값(MAC + hostname)으로 32바이트 Fernet 키 파생."""
    import uuid
    raw = f"{uuid.getnode()}-{platform.node()}-awt-v1"
    digest = hashlib.sha256(raw.encode()).digest()
    import base64
    return base64.urlsafe_b64encode(digest)


def _fernet() -> Fernet:
    return Fernet(_machine_key())


def _load_payload() -> dict:
    """저장된 settings dict 로드. 없거나 깨졌으면 빈 dict 반환."""
    if not _CONFIG_FILE.exists():
        return {}
    try:
        decrypted = _fernet().decrypt(_CONFIG_FILE.read_bytes())
        data = json.loads(decrypted)
        # 구 형식 마이그레이션: {"api_key": "..."} → anthropic_key
        if "api_key" in data and "anthropic_key" not in data:
            data["anthropic_key"] = data.pop("api_key")
        return data
    except Exception:
        return {}


def _save_payload(payload: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    encrypted = _fernet().encrypt(json.dumps(payload).encode())
    _CONFIG_FILE.write_bytes(encrypted)


# ── Public API ──────────────────────────────────────────────────────────

def get_active_provider() -> str:
    """현재 활성 provider 이름. .env의 LLM_PROVIDER가 있으면 그쪽 우선."""
    env = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if env in VALID_PROVIDERS:
        return env
    data = _load_payload()
    p = data.get("active_provider", _DEFAULT_PROVIDER)
    return p if p in VALID_PROVIDERS else _DEFAULT_PROVIDER


def set_active_provider(provider: str) -> None:
    """활성 provider 전환. 키는 그대로 보존."""
    if provider not in VALID_PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Use one of {VALID_PROVIDERS}")
    data = _load_payload()
    data["active_provider"] = provider
    _save_payload(data)


def save_api_key(api_key: str, provider: str | None = None) -> None:
    """provider의 API 키 저장. provider 미지정 시 현재 활성 provider에 저장."""
    provider = provider or get_active_provider()
    if provider not in VALID_PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")
    data = _load_payload()
    data[_KEY_FIELD[provider]] = api_key
    # 활성 provider도 갱신 (UI에서 키 저장은 보통 그 provider를 쓴다는 의미)
    data["active_provider"] = provider
    _save_payload(data)


def load_api_key(provider: str | None = None) -> str | None:
    """provider의 API 키 로드. provider 미지정 시 현재 활성 provider 키 반환.

    .env 환경변수가 있으면 그쪽이 우선:
        ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY
    """
    provider = provider or get_active_provider()
    if provider not in VALID_PROVIDERS:
        return None

    # 환경변수 우선
    env_var = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
    }[provider]
    env_val = os.environ.get(env_var, "").strip()
    if env_val:
        return env_val

    # 암호화 저장소
    data = _load_payload()
    return data.get(_KEY_FIELD[provider]) or None


def delete_api_key(provider: str | None = None) -> None:
    """provider의 API 키만 삭제. 다른 provider 키와 active_provider는 보존."""
    provider = provider or get_active_provider()
    if provider not in VALID_PROVIDERS:
        return
    data = _load_payload()
    data.pop(_KEY_FIELD[provider], None)
    _save_payload(data)
