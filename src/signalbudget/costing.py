from __future__ import annotations

from typing import Any

DAYS_PER_MONTH = 30


def estimate_monthly_source_costs(
    volume_profile: dict[str, Any],
    pricing_profile: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    prices = _price_by_log_tier(pricing_profile)
    estimates: dict[str, dict[str, Any]] = {}

    for source in volume_profile.get("volume_profiles", []):
        source_id = source["source_id"]
        status = source.get("measurement_status", "pending")
        gb_per_day = source.get("estimated_gb_per_day")
        log_tier = source.get("pricing_log_tier", "Analytics Logs")
        unit_price = prices.get(log_tier)

        if status == "pending" or gb_per_day is None or unit_price is None:
            estimates[source_id] = {
                "source_id": source_id,
                "measurement_status": status,
                "estimated_monthly_gb": None,
                "estimated_monthly_cost_usd": None,
                "estimated_monthly_proxy_gb": None,
                "estimated_monthly_proxy_cost_usd": None,
                "pricing_log_tier": log_tier,
                "cost_estimate_kind": "XML_EXPORT_SIZE_PROXY",
                "cost_status": "VOLUME_MEASUREMENT_PENDING",
            }
            continue

        monthly_gb = float(gb_per_day) * DAYS_PER_MONTH
        monthly_cost = monthly_gb * float(unit_price)
        estimates[source_id] = {
            "source_id": source_id,
            "measurement_status": status,
            "estimated_monthly_gb": monthly_gb,
            "estimated_monthly_cost_usd": monthly_cost,
            "estimated_monthly_proxy_gb": monthly_gb,
            "estimated_monthly_proxy_cost_usd": monthly_cost,
            "pricing_log_tier": log_tier,
            "unit_price_per_gb_usd": unit_price,
            "cost_estimate_kind": "XML_EXPORT_SIZE_PROXY",
            "cost_status": _cost_status_for_measurement(status),
        }

    return estimates


def summarize_selected_source_costs(
    selected_sources: list[str],
    source_costs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if not selected_sources:
        return {
            "known_monthly_cost_usd": 0.0,
            "estimated_monthly_cost_usd": 0.0,
            "known_monthly_proxy_cost_usd": 0.0,
            "estimated_monthly_proxy_cost_usd": 0.0,
            "cost_estimate_kind": "XML_EXPORT_SIZE_PROXY",
            "cost_status": "NO_SOURCES_SELECTED",
            "missing_volume_sources": [],
        }

    known_cost = 0.0
    missing: list[str] = []
    statuses: set[str] = set()
    for source_id in selected_sources:
        estimate = source_costs.get(source_id)
        if estimate is None or estimate.get("estimated_monthly_cost_usd") is None:
            missing.append(source_id)
            continue
        known_cost += float(estimate["estimated_monthly_cost_usd"])
        statuses.add(str(estimate.get("cost_status", "ESTIMATED")))

    if missing and known_cost == 0:
        return {
            "known_monthly_cost_usd": None,
            "estimated_monthly_cost_usd": None,
            "known_monthly_proxy_cost_usd": None,
            "estimated_monthly_proxy_cost_usd": None,
            "cost_estimate_kind": "XML_EXPORT_SIZE_PROXY",
            "cost_status": "VOLUME_MEASUREMENT_PENDING",
            "missing_volume_sources": missing,
        }

    if missing:
        return {
            "known_monthly_cost_usd": round(known_cost, 8),
            "estimated_monthly_cost_usd": None,
            "known_monthly_proxy_cost_usd": round(known_cost, 8),
            "estimated_monthly_proxy_cost_usd": None,
            "cost_estimate_kind": "XML_EXPORT_SIZE_PROXY",
            "cost_status": "PARTIAL_VOLUME_MEASUREMENT",
            "missing_volume_sources": missing,
        }

    status = _combined_cost_status(statuses)
    return {
        "known_monthly_cost_usd": round(known_cost, 8),
        "estimated_monthly_cost_usd": round(known_cost, 8),
        "known_monthly_proxy_cost_usd": round(known_cost, 8),
        "estimated_monthly_proxy_cost_usd": round(known_cost, 8),
        "cost_estimate_kind": "XML_EXPORT_SIZE_PROXY",
        "cost_status": status,
        "missing_volume_sources": [],
    }


def cost_boundary_text(source_costs: dict[str, dict[str, Any]]) -> str:
    parts = []
    for source_id, cost in sorted(source_costs.items()):
        measurement_status = cost.get("measurement_status", "pending")
        cost_status = cost.get("cost_status", "UNKNOWN")
        estimated_cost = cost.get("estimated_monthly_proxy_cost_usd")
        if estimated_cost is None:
            parts.append(f"{source_id}: {measurement_status}, {cost_status}")
        else:
            parts.append(
                f"{source_id}: {measurement_status}, {cost_status}, "
                f"${float(estimated_cost):.8f}/month XML export proxy"
            )
    return "Cost measurement status - " + "; ".join(parts)


def _price_by_log_tier(pricing_profile: dict[str, Any]) -> dict[str, float]:
    return {
        meter["log_tier"]: float(meter["unit_price"])
        for meter in pricing_profile.get("meters", [])
    }


def _cost_status_for_measurement(measurement_status: str) -> str:
    if measurement_status == "lab_24h_measurement":
        return "ESTIMATED_FROM_24H_LAB_MEASUREMENT"
    if measurement_status == "lab_sample_estimate":
        return "ESTIMATED_FROM_LAB_SAMPLE"
    return "ESTIMATED"


def _combined_cost_status(statuses: set[str]) -> str:
    if "ESTIMATED_FROM_24H_LAB_MEASUREMENT" in statuses:
        return "ESTIMATED_FROM_24H_LAB_MEASUREMENT"
    if "ESTIMATED_FROM_LAB_SAMPLE" in statuses:
        return "ESTIMATED_FROM_LAB_SAMPLE"
    return "ESTIMATED"
