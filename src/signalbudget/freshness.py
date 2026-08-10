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
    lines = [
        f"Pricing profile retrieved: `{freshness['retrieved_at']}` "
        f"(max age `{freshness['max_age_days']}` days)"
    ]
    if freshness.get("verified_at") is not None:
        lines.append(
            f"Last verified against the source API: `{freshness['verified_at']}` "
            f"(freshness measured from `{freshness['freshness_basis']}`)"
        )
    lines.append(FRESHNESS_IS_EVALUATED_AT_RUN_TIME)
    return lines


def pricing_freshness(
    pricing_profile: dict[str, Any],
    as_of: datetime | None = None,
) -> dict[str, object]:
    """Age a pricing profile against its own ``max_age_days``.

    Age is measured from the most recent evidence that the prices were current,
    which is the later of ``retrieved_at`` and ``verified_at``. Re-querying the
    source API and finding the meters unchanged is a real confirmation, so a
    profile that records one is not stale merely because the original download
    was long ago. ``verified_at`` is optional; without it this reduces to the
    retrieval date.
    """
    retrieved_at = _parse_utc(str(pricing_profile["retrieved_at"]))
    raw_verified_at = pricing_profile.get("verified_at")
    verified_at = (
        _parse_utc(str(raw_verified_at)) if raw_verified_at is not None else None
    )

    anchor = retrieved_at
    basis = "retrieved_at"
    if verified_at is not None and verified_at > retrieved_at:
        anchor = verified_at
        basis = "verified_at"

    current = as_of or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    else:
        current = current.astimezone(UTC)
    age = current - anchor
    age_days = age.days
    max_age_days = int(pricing_profile["max_age_days"])
    common: dict[str, object] = {
        "retrieved_at": retrieved_at.isoformat().replace("+00:00", "Z"),
        "verified_at": (
            verified_at.isoformat().replace("+00:00", "Z")
            if verified_at is not None
            else None
        ),
        "freshness_basis": basis,
        "age_days": age_days,
        "max_age_days": max_age_days,
    }
    if age < timedelta(0):
        return {
            **common,
            "fresh": False,
            "status": PRICING_STALE,
            "reason": "PRICING_RETRIEVED_IN_FUTURE",
        }
    fresh = age <= timedelta(days=max_age_days)
    return {
        **common,
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
