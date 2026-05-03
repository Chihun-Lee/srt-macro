"""Secret storage for SRT credentials and card info.

Backed by macOS Keychain via the `keyring` library
(`keyring.backends.macOS.Keyring`, Security.framework).

The whole credential blob is JSON-encoded and stored as a single
Keychain item under (service=KEYRING_SERVICE, username=KEYRING_USER).

Encryption-at-rest is handled by macOS — the value is sealed with the
user's login keychain master key and never written to disk in plaintext.
"""
from __future__ import annotations

import json
from typing import Optional

import keyring
from pydantic import BaseModel, Field

KEYRING_SERVICE = "srt-macro"
KEYRING_USER = "config"


class Credentials(BaseModel):
    srt_id: str = Field(min_length=1)
    srt_password: str = Field(min_length=1)
    card_number: str = Field(min_length=12, max_length=19)
    card_password: str = Field(min_length=2, max_length=2)
    card_validation: str = Field(min_length=6, max_length=10)
    card_expire: str = Field(min_length=4, max_length=4)
    card_type: str = Field(default="J", pattern="^[JS]$")
    card_installment: int = Field(default=0, ge=0, le=24)


def _read_blob() -> Optional[str]:
    return keyring.get_password(KEYRING_SERVICE, KEYRING_USER)


def exists() -> bool:
    return _read_blob() is not None


def load() -> Optional[Credentials]:
    blob = _read_blob()
    if not blob:
        return None
    try:
        return Credentials.model_validate_json(blob)
    except Exception:
        return None


def save(creds: Credentials) -> None:
    payload = {
        "srt_id": creds.srt_id,
        "srt_password": creds.srt_password,
        "card_number": creds.card_number.replace("-", "").replace(" ", ""),
        "card_password": creds.card_password,
        "card_validation": creds.card_validation,
        "card_expire": creds.card_expire,
        "card_type": creds.card_type,
        "card_installment": creds.card_installment,
    }
    keyring.set_password(KEYRING_SERVICE, KEYRING_USER, json.dumps(payload))


def clear() -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
    except keyring.errors.PasswordDeleteError:
        pass


def public_status() -> dict:
    """Return non-sensitive metadata about saved credentials."""
    creds = load()
    if not creds:
        return {"configured": False}
    masked = "*" * (len(creds.card_number) - 4) + creds.card_number[-4:]
    return {
        "configured": True,
        "srt_id": creds.srt_id,
        "card_last4": creds.card_number[-4:],
        "card_masked": masked,
        "card_type": creds.card_type,
        "card_installment": creds.card_installment,
        "storage": "macOS Keychain",
    }
