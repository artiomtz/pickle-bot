import re

from backend.utils.time_utils import parse_iso_utc, to_iso_utc

ID_MAX_LEN = 32
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
ENGLISH_PATTERN = re.compile(r"^[\x20-\x7E]+$")


def validate_id(value: str) -> str:
    if not ID_PATTERN.match(value):
        raise ValueError("Invalid chat id format")
    if len(value) > ID_MAX_LEN:
        raise ValueError("Invalid chat id length")
    return id


def validate_since(value: str) -> str:
    try:
        dt = parse_iso_utc(value)
    except ValueError:
        raise ValueError("Invalid ISO timestamp")
    return to_iso_utc(dt)


def validate_days(value: int) -> int:
    if not isinstance(value, int):
        raise ValueError("Days must be an integer")
    if value <= 0:
        raise ValueError("Days must be positive")
    if value > 365:
        raise ValueError("Days too large")
    return value


def validate_limit(value: int) -> int:
    if not isinstance(value, int):
        raise ValueError("Limit must be an integer")
    if value <= 0:
        raise ValueError("Limit must be positive")
    if value > 1000:
        raise ValueError("Limit too large")
    return value


def validate_english(text: str) -> bool:
    if not ENGLISH_PATTERN.match(text):
        return False

    return True
