"""API 키 Fernet 암호화 저장/로드 (D42)."""
import os
import json
import hashlib
import platform
from pathlib import Path
from cryptography.fernet import Fernet

_CONFIG_DIR = Path.home() / ".awt"
_CONFIG_FILE = _CONFIG_DIR / "settings.enc"


def _machine_key() -> bytes:
    """머신 고유값(MAC + hostname)으로 32바이트 Fernet 키 파생."""
    import uuid
    raw = f"{uuid.getnode()}-{platform.node()}-awt-v1"
    digest = hashlib.sha256(raw.encode()).digest()
    import base64
    return base64.urlsafe_b64encode(digest)


def _fernet() -> Fernet:
    return Fernet(_machine_key())


def save_api_key(api_key: str) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"api_key": api_key}).encode()
    encrypted = _fernet().encrypt(payload)
    _CONFIG_FILE.write_bytes(encrypted)


def load_api_key() -> str | None:
    if not _CONFIG_FILE.exists():
        return None
    try:
        decrypted = _fernet().decrypt(_CONFIG_FILE.read_bytes())
        return json.loads(decrypted)["api_key"]
    except Exception:
        return None


def delete_api_key() -> None:
    if _CONFIG_FILE.exists():
        _CONFIG_FILE.unlink()
