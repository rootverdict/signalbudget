from __future__ import annotations

from typing import Any


def analyze_pareto(configurations: list[dict[str, Any]]) -> dict[str, Any]:
    complete_cost = [
        config
        for config in configurations
        if config.get("estimated_monthly_cost_usd") is not None
    ]
    incomplete_cost = [
        config
        for config in configurations
        if config.get("estimated_monthly_cost_usd") is None
    ]

    complete_results = [
        _annotate_complete_configuration(config, complete_cost)
        for config in complete_cost
    ]
    incomplete_results = [
        _annotate_incomplete_configuration(config)
        for config in incomplete_cost
    ]
    all_results = sorted(
        complete_results + incomplete_results,
        key=lambda item: (
            item["pareto_status"] != "NON_DOMINATED",
            item["estimated_monthly_cost_usd"] is None,
            item["estimated_monthly_cost_usd"]
            if item["estimated_monthly_cost_usd"] is not None
            else float("inf"),
            item["configuration_id"],
        ),
    )

    return {
        "schema_version": "1.0",
        "analysis_method": (
            "Pareto frontier over cost, validated detection coverage, and "
            "investigation utility. Lower cost is better; higher coverage and "
            "utility are better."
        ),
        "cost_boundary": _cost_boundary(len(incomplete_cost)),
        "configuration_count": len(configurations),
        "complete_cost_configuration_count": len(complete_cost),
        "partial_cost_configuration_count": len(incomplete_cost),
        "non_dominated": [
            config
            for config in all_results
            if config["pareto_status"] == "NON_DOMINATED"
        ],
        "pending_cost": [
            config
            for config in all_results
            if config["pareto_status"] == "PARETO_PENDING_COST"
        ],
        "dominated": [
            config
            for config in all_results
            if config["pareto_status"] == "DOMINATED"
        ],
        "configurations": all_results,
    }


def _cost_boundary(incomplete_count: int) -> str:
    if incomplete_count == 0:
        return (
            "All configurations have complete lab-derived cost estimates. Pareto "
            "status is final within the current three-source lab measurement set."
        )
    return (
        "Only complete-cost configurations can be assigned a final Pareto status. "
        "Partial-cost configurations are listed separately until missing source "
        "volumes are measured."
    )


def dominates(candidate: dict[str, Any], other: dict[str, Any]) -> bool:
    candidate_cost = candidate.get("estimated_monthly_cost_usd")
    other_cost = other.get("estimated_monthly_cost_usd")
    if candidate_cost is None or other_cost is None:
        return False

    candidate_metrics = _metrics(candidate)
    other_metrics = _metrics(other)

    no_worse = (
        float(candidate_cost) <= float(other_cost)
        and candidate_metrics["validated_detection_count"]
        >= other_metrics["validated_detection_count"]
        and candidate_metrics["investigation_question_ready_count"]
        >= other_metrics["investigation_question_ready_count"]
    )
    strictly_better = (
        float(candidate_cost) < float(other_cost)
        or candidate_metrics["validated_detection_count"]
        > other_metrics["validated_detection_count"]
        or candidate_metrics["investigation_question_ready_count"]
        > other_metrics["investigation_question_ready_count"]
    )
    return no_worse and strictly_better


def _annotate_complete_configuration(
    config: dict[str, Any],
    complete_cost_configs: list[dict[str, Any]],
) -> dict[str, Any]:
    dominators = [
        other["configuration_id"]
        for other in complete_cost_configs
        if other is not config and dominates(other, config)
    ]
    annotated = _summary(config)
    if dominators:
        annotated["pareto_status"] = "DOMINATED"
        annotated["dominated_by"] = dominators
    else:
        annotated["pareto_status"] = "NON_DOMINATED"
        annotated["dominated_by"] = []
    return annotated


def _annotate_incomplete_configuration(config: dict[str, Any]) -> dict[str, Any]:
    annotated = _summary(config)
    annotated["pareto_status"] = "PARETO_PENDING_COST"
    annotated["dominated_by"] = []
    annotated["pending_reason"] = (
        "Full Pareto status is pending because one or more selected sources "
        "are missing byte-size volume measurements."
    )
    return annotated


def _summary(config: dict[str, Any]) -> dict[str, Any]:
    metrics = _metrics(config)
    return {
        "configuration_id": config["configuration_id"],
        "selected_sources": config["selected_sources"],
        "estimated_monthly_cost_usd": config.get("estimated_monthly_cost_usd"),
        "known_monthly_cost_usd": config.get("known_monthly_cost_usd"),
        "estimated_monthly_proxy_cost_usd": config.get(
            "estimated_monthly_proxy_cost_usd"
        ),
        "known_monthly_proxy_cost_usd": config.get("known_monthly_proxy_cost_usd"),
        "cost_estimate_kind": config.get("cost_estimate_kind"),
        "cost_status": config["cost_status"],
        "missing_volume_sources": config.get("missing_volume_sources", []),
        **metrics,
    }


def _metrics(config: dict[str, Any]) -> dict[str, int]:
    return {
        "validated_detection_count": int(config.get("validated_detection_count", 0)),
        "telemetry_ready_detection_count": int(
            config.get("telemetry_ready_detection_count", 0)
        ),
        "investigation_question_ready_count": int(
            config.get("investigation_question_ready_count", 0)
        ),
    }


def render_pareto_markdown(analysis: dict[str, Any]) -> str:
    lines = [
        "# SignalBudget Pareto Analysis",
        "",
        f"Configuration count: `{analysis['configuration_count']}`",
        f"Complete-cost configurations: `{analysis['complete_cost_configuration_count']}`",
        f"Partial-cost configurations: `{analysis['partial_cost_configuration_count']}`",
    ]
    if "pricing_status" in analysis:
        lines.extend(["", f"Pricing status: `{analysis['pricing_status']}`"])
    lines.extend(
        [
            "",
            "## Non-Dominated Complete-Cost Configurations",
            "",
        ]
    )
    for config in analysis["non_dominated"]:
        lines.append(_config_line(config))

    if analysis["pending_cost"]:
        lines.extend(["", "## Pending Cost Configurations", ""])
        for config in analysis["pending_cost"]:
            lines.append(_config_line(config))

    if analysis["dominated"]:
        lines.extend(["", "## Dominated Complete-Cost Configurations", ""])
        for config in analysis["dominated"]:
            lines.append(_config_line(config))

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            analysis["cost_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def _config_line(config: dict[str, Any]) -> str:
    proxy_cost = config.get(
        "estimated_monthly_proxy_cost_usd",
        config.get("estimated_monthly_cost_usd"),
    )
    return (
        f"- `{config['configuration_id']}`: status `{config['pareto_status']}`, "
        f"proxy cost `{proxy_cost}`, "
        f"validated detections `{config['validated_detection_count']}`, "
        f"investigation questions `{config['investigation_question_ready_count']}`"
    )
