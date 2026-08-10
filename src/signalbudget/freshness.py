from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

PRICING_FRESH = "PRICING_FRESH"
PRICING_STALE = "PRICING_STALE"

FRESHNESS_IS_EVALUATED_AT_RUN_TIME = (
    "Freshness is evaluated when the report is generated, so this file records "
    "the status as of its own generation date rather than today's."
)


def pricing_provenance_lines(freshness: dict[str, object]) -> list[str]:
    """Render the stable half of the pricing block.

    Deliberately excludes ``age_days``: these lines are diffed against the
    committed reports in CI, and anything that moves with the calendar would
    break that check the next day.
    """
    return [
        f"Pricing profile retrieved: `{freshness['retrieved_at']}` "
        f"(max age `{freshness['max_age_days']}` days)",
        FRESHNESS_IS_EVALUATED_AT_RUN_TIME,
    ]


def pricing_freshness(
    pricing_profile: dict[str, Any],
    as_of: datetime | None = None,
) -> dict[str, object]:
    retrieved_at = _parse_utc(str(pricing_profile["retrieved_at"]))
    current = as_of or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    else:
        current = current.astimezone(UTC)
    age = current - retrieved_at
    age_days = age.days
    max_age_days = int(pricing_profile["max_age_days"])
    if age < timedelta(0):
        return {
            "retrieved_at": retrieved_at.isoformat().replace("+00:00", "Z"),
            "age_days": age_days,
            "max_age_days": max_age_days,
            "fresh": False,
            "status": PRICING_STALE,
            "reason": "PRICING_RETRIEVED_IN_FUTURE",
        }
    fresh = age <= timedelta(days=max_age_days)
    return {
        "retrieved_at": retrieved_at.isoformat().replace("+00:00", "Z"),
        "age_days": age_days,
        "max_age_days": max_age_days,
        "fresh": fresh,
        "status": PRICING_FRESH if fresh else PRICING_STALE,
        "reason": "PRICING_WITHIN_MAX_AGE"
        if fresh
        else "PRICING_OLDER_THAN_MAX_AGE",
    }


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
