from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

PRICING_FRESH = "PRICING_FRESH"
PRICING_STALE = "PRICING_STALE"


def pricing_freshness(
    pricing_profile: dict[str, Any],
    as_of: datetime | None = None,
) -> dict[str, object]:
    retrieved_at = _parse_utc(str(pricing_profile["retrieved_at"]))
    current = as_of or datetime.now(UTC)
    age_days = (current - retrieved_at).days
    max_age_days = int(pricing_profile["max_age_days"])
    if age_days < 0:
        return {
            "retrieved_at": retrieved_at.isoformat().replace("+00:00", "Z"),
            "age_days": age_days,
            "max_age_days": max_age_days,
            "fresh": False,
            "status": PRICING_STALE,
            "reason": "PRICING_RETRIEVED_IN_FUTURE",
        }
    return {
        "retrieved_at": retrieved_at.isoformat().replace("+00:00", "Z"),
        "age_days": age_days,
        "max_age_days": max_age_days,
        "fresh": age_days <= max_age_days,
        "status": PRICING_FRESH if age_days <= max_age_days else PRICING_STALE,
        "reason": "PRICING_WITHIN_MAX_AGE"
        if age_days <= max_age_days
        else "PRICING_OLDER_THAN_MAX_AGE",
    }


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
