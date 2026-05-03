"""Secret storage for SRT credentials and card info.

Saved to ~/.config/k-skill/srt_macro.env with mode 0600.
Never logged, never returned via API in plaintext.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

CONFIG_DIR = Path.home() / ".config" / "k-skill"
CONFIG_FILE = CONFIG_DIR / "srt_macro.env"

FIELDS = (
    "SRT_ID",
    "SRT_PASSWORD",
    "CARD_NUMBER",
    "CARD_PASSWORD",
    "CARD_VALIDATION",
    "CARD_EXPIRE",
    "CARD_TYPE",
    "CARD_INSTALLMENT",
)


class Credentials(BaseModel):
    srt_id: str = Field(min_length=1)
    srt_password: str = Field(min_length=1)
    card_number: str = Field(min_length=12, max_length=19)
    card_password: str = Field(min_length=2, max_length=2)
    card_validation: str = Field(min_length=6, max_length=10)
    card_expire: str = Field(min_length=4, max_length=4)
    card_type: str = Field(default="J", pattern="^[JS]$")
    card_installment: int = Field(default=0, ge=0, le=24)


def exists() -> bool:
    return CONFIG_FILE.is_file()


def load() -> Optional[Credentials]:
    if not exists():
        return None
    data: dict[str, str] = {}
    for line in CONFIG_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    try:
        return Credentials(
            srt_id=data["SRT_ID"],
            srt_password=data["SRT_PASSWORD"],
            card_number=data["CARD_NUMBER"],
            card_password=data["CARD_PASSWORD"],
            card_validation=data["CARD_VALIDATION"],
            card_expire=data["CARD_EXPIRE"],
            card_type=data.get("CARD_TYPE", "J"),
            card_installment=int(data.get("CARD_INSTALLMENT", "0")),
        )
    except KeyError:
        return None


def save(creds: Credentials) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    body = (
        f"SRT_ID={creds.srt_id}\n"
        f"SRT_PASSWORD={creds.srt_password}\n"
        f"CARD_NUMBER={creds.card_number.replace('-', '').replace(' ', '')}\n"
        f"CARD_PASSWORD={creds.card_password}\n"
        f"CARD_VALIDATION={creds.card_validation}\n"
        f"CARD_EXPIRE={creds.card_expire}\n"
        f"CARD_TYPE={creds.card_type}\n"
        f"CARD_INSTALLMENT={creds.card_installment}\n"
    )
    CONFIG_FILE.write_text(body)
    os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)


def public_status() -> dict:
    """Return non-sensitive metadata about saved credentials."""
    if not exists():
        return {"configured": False}
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
    }
