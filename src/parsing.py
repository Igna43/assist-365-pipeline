"""Parsing for the messy source payloads.

Slash dates are day-first. The claims feed mixes ``DD/MM/YYYY`` and ``YYYY-MM-DD``,
and several slash values have a day greater than 12, so they cannot be month-first.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

_ISO_DAY = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
_DMY = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
_MISSING = {"", "nan", "none", "null", "infinity", "-infinity"}


def parse_date(value: object) -> str | None:
    """Return an ISO date ``YYYY-MM-DD`` or None when the value is not a real date."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _MISSING:
        return None
    iso = _ISO_DAY.match(text)
    if iso and (len(text) == 10 or text[10] in "T "):
        year, month, day = (int(part) for part in iso.groups())
        return _valid_iso(year, month, day)
    dmy = _DMY.match(text)
    if dmy:
        day, month, year = (int(part) for part in dmy.groups())
        return _valid_iso(year, month, day)
    return None


def parse_timestamp(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _MISSING:
        return None
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return text


def decimal_string(value: object) -> str | None:
    """Canonical decimal text for BigQuery NUMERIC. Rejects NaN and blank currency amounts."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    text = str(value).strip()
    if text.lower() in _MISSING:
        return None
    try:
        Decimal(text)
    except InvalidOperation:
        return None
    return text


def clean_currency(value: object) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    text = str(value).strip().upper()
    if text.lower() in _MISSING:
        return None
    return text


def loads_payload(text: str) -> object:
    """JSON load that turns non-standard NaN/Infinity into None.

    The claims feed emits ``NaN`` as a currency on some rows. BigQuery rejects that token.
    """
    import json

    return json.loads(text, parse_constant=lambda _constant: None)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_watermark(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = str(value).strip()
    if not text:
        return None
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_after(updated_at: object, watermark: str) -> bool:
    left = parse_timestamp(updated_at)
    if left is None:
        return False
    return format_watermark(left) > watermark


def _valid_iso(year: int, month: int, day: int) -> str | None:
    try:
        datetime(year, month, day)
    except ValueError:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"
