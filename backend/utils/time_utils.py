from datetime import datetime, timezone


def parse_iso_utc(value: str) -> datetime:
    cleaned = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt


def to_iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()
