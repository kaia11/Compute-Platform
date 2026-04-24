from __future__ import annotations

from datetime import datetime

from .config import TIMEZONE


def now_iso() -> str:
    return datetime.now(TIMEZONE).isoformat(timespec="seconds")


def parse_iso(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def round2(value: float | None) -> float | None:
    return None if value is None else round(value + 1e-9, 2)


def mask_phone(phone: str | None) -> str:
    if not phone:
        return ""
    if len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def duration_hours_from_seconds(duration_seconds: int | None) -> float:
    if not duration_seconds:
        return 0.0
    return round2(duration_seconds / 3600) or 0.0


def card_label(card_type: str, cabinet_type: str) -> str:
    if card_type == "4090" and cabinet_type == "单卡机柜":
        return "RTX 4090 1卡机"
    if card_type == "4090" and cabinet_type == "双卡机柜":
        return "RTX 4090 2卡机"
    if card_type == "910B":
        return "昇腾 910B 推理型"
    if card_type == "910C":
        return "昇腾 910C 训练型"
    return f"{card_type} {cabinet_type}"
