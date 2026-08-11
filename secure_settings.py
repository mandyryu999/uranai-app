import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select

from database import SessionLocal
from models import AppSetting

KEY_PATH = Path(os.environ.get("APP_SETTINGS_KEY_PATH", "/app-secrets/settings.key"))
OPENAI_API_KEY_SETTING = "openai_api_key"


def _fernet() -> Fernet:
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if KEY_PATH.exists():
        key = KEY_PATH.read_bytes().strip()
    else:
        key = Fernet.generate_key()
        KEY_PATH.write_bytes(key)
        try:
            os.chmod(KEY_PATH, 0o600)
        except OSError:
            pass
    return Fernet(key)


def set_secret(key: str, value: str) -> None:
    encrypted = _fernet().encrypt(value.encode("utf-8")).decode("ascii")
    with SessionLocal() as db:
        setting = db.scalar(select(AppSetting).where(AppSetting.key == key))
        if setting is None:
            setting = AppSetting(key=key, encrypted_value=encrypted)
            db.add(setting)
        else:
            setting.encrypted_value = encrypted
        db.commit()


def get_secret(key: str) -> str | None:
    with SessionLocal() as db:
        setting = db.scalar(select(AppSetting).where(AppSetting.key == key))
        if setting is None:
            return None
        encrypted = setting.encrypted_value
    try:
        return _fernet().decrypt(encrypted.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None


def delete_secret(key: str) -> bool:
    with SessionLocal() as db:
        setting = db.scalar(select(AppSetting).where(AppSetting.key == key))
        if setting is None:
            return False
        db.delete(setting)
        db.commit()
        return True


def get_openai_api_key() -> str | None:
    stored = get_secret(OPENAI_API_KEY_SETTING)
    if stored:
        return stored
    return os.environ.get("OPENAI_API_KEY") or None


def get_openai_api_key_status() -> dict:
    stored = get_secret(OPENAI_API_KEY_SETTING)
    if stored:
        return {
            "configured": True,
            "source": "app",
            "masked": _mask(stored),
        }
    env_key = os.environ.get("OPENAI_API_KEY") or ""
    if env_key:
        return {
            "configured": True,
            "source": "environment",
            "masked": _mask(env_key),
        }
    return {"configured": False, "source": None, "masked": None}


def _mask(value: str) -> str:
    if len(value) <= 8:
        return "••••••••"
    return f"{value[:4]}••••••••{value[-4:]}"
