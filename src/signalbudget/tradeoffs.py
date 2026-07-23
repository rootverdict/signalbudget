from __future__ import annotations

from typing import Any

from signalbudget.configurations import enumerate_source_configurations
from signalbudget.costing import estimate_monthly_source_costs
from signalbudget.coverage import detection_readiness, investigation_readiness
from signalbudget.freshness import pricing_freshness
from signalbudget.loaders import CatalogBundle
from signalbudget.pareto import analyze_pareto

LAB_ESTIMATE_CAVEAT = (
    "Cost estimates are lab-derived from 24-hour VM measurements and are not "
    "production forecasts."
)


def build_tradeoff_report(
    bundle: CatalogBundle,
    validated_rule_ids: set[str] | None = None,
) -> dict[str, Any]:
    freshness = pricing_freshness(bundle.pricing)
    source_costs = estimate_monthly_source_costs(
        bundle.source_volumes,
        bundle.pricing,
    )
    configurations = enumerate_source_configurations(
        bundle.log_sources,
        bundle.detection_dependencies,
        bundle.investigation_questions,
        source_costs,
        validated_rule_ids or set(),
    )
    pareto = analyze_pareto(configurations)
    removal_losses = source_removal_losses(
        bundle.log_sources,
        bundle.detection_dependencies,
        bundle.investigation_questions,
    )
    narratives = frontier_tradeoffs(
        configurations,
        pareto["non_dominated"],
        bundle.detection_dependencies,
        bundle.investigation_questions,
    )

    return {
        "schema_version": "1.0",
        "pricing_status": freshness["status"],
        "pricing": freshness,
        "evidence_caveat": LAB_ESTIMATE_CAVEAT,
        "pareto_summary": {
            "configuration_count": pareto["configuration_count"],
            "complete_cost_configuration_count": pareto[
                "complete_cost_configuration_count"
            ],
            "partial_cost_configuration_count": pareto[
                "partial_cost_configuration_count"
            ],
            "non_dominated_configuration_ids": [
                config["configuration_id"] for config in pareto["non_dominated"]
            ],
            "dominated_configuration_ids": [
                config["configuration_id"] for config in pareto["dominated"]
            ],
        },
        "source_removal_losses": removal_losses,
        "frontier_tradeoffs": narratives,
    }


def source_removal_losses(
    log_source_catalog: dict[str, Any],
    detection_catalog: dict[str, Any],
    question_catalog: dict[str, Any],
) -> list[dict[str, Any]]:
    all_sources = {source["id"] for source in log_source_catalog.get("sources", [])}
    baseline_detections = detection_readiness(
        detection_catalog,
        all_sources,
        log_source_catalog,
    )
    baseline_questions = investigation_readiness(
        question_catalog,
        all_sources,
        log_source_catalog,
    )
    losses: list[dict[str, Any]] = []
    for source_id in sorted(all_sources):
        remaining = all_sources - {source_id}
        remaining_detections = detection_readiness(
            detection_catalog,
            remaining,
            log_source_catalog,
        )
        remaining_questions = investigation_readiness(
            question_catalog,
            remaining,
            log_source_catalog,
        )
        losses.append(
            {
                "removed_source": source_id,
                "lost_detections": [
                    _detection_summary(detection)
                    for detection in detection_catalog.get("detections", [])
                    if baseline_detections[detection["id"]]
                    and not remaining_detections[detection["id"]]
                ],
                "lost_investigation_questions": [
                    _question_summary(question)
                    for question in question_catalog.get("questions", [])
                    if baseline_questions[question["id"]]
                    and not remaining_questions[question["id"]]
                ],
            }
        )
    return losses


def frontier_tradeoffs(
    configurations: list[dict[str, Any]],
    non_dominated: list[dict[str, Any]],
    detection_catalog: dict[str, Any],
    question_catalog: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = {config["configuration_id"]: config for config in configurations}
    narratives: list[dict[str, Any]] = []
    frontier = [by_id[config["configuration_id"]] for config in non_dominated]
    if not frontier:
        return narratives

    first = frontier[0]
    narratives.append(
        {
            "type": "baseline",
            "configuration_id": first["configuration_id"],
            "estimated_monthly_cost_usd": first["estimated_monthly_cost_usd"],
            "estimated_monthly_proxy_cost_usd": first[
                "estimated_monthly_proxy_cost_usd"
            ],
            "cost_estimate_kind": first["cost_estimate_kind"],
            "validated_detection_count": first["validated_detection_count"],
            "investigation_question_ready_count": first[
                "investigation_question_ready_count"
            ],
            "narrative": _baseline_text(first),
        }
    )

    for previous, current in zip(frontier, frontier[1:], strict=False):
        transition = _frontier_transition(
            previous,
            current,
            detection_catalog,
            question_catalog,
        )
        narratives.append(transition)

    return narratives


def render_tradeoff_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# SignalBudget Tradeoff Explanations",
        "",
        f"Pricing status: `{report['pricing_status']}`",
        "",
        "## Evidence Caveat",
        "",
        report["evidence_caveat"],
        "",
        "## Source Removal Losses",
        "",
    ]
    for loss in report["source_removal_losses"]:
        lines.append(f"### Remove `{loss['removed_source']}`")
        lines.append("")
        lines.append("Lost detections:")
        lines.extend(_id_lines(loss["lost_detections"]))
        lines.append("")
        lines.append("Lost investigation questions:")
        lines.extend(_id_lines(loss["lost_investigation_questions"]))
        lines.append("")

    lines.extend(["## Frontier Tradeoffs", ""])
    for tradeoff in report["frontier_tradeoffs"]:
        lines.append(f"- {tradeoff['narrative']}")

    lines.append("")
    return "\n".join(lines)


def _frontier_transition(
    previous: dict[str, Any],
    current: dict[str, Any],
    detection_catalog: dict[str, Any],
    question_catalog: dict[str, Any],
) -> dict[str, Any]:
    previous_sources = set(previous["selected_sources"])
    current_sources = set(current["selected_sources"])
    previous_detections = previous["detection_readiness"]
    current_detections = current["detection_readiness"]
    previous_questions = previous["investigation_readiness"]
    current_questions = current["investigation_readiness"]
    cost_delta = round(
        float(current["estimated_monthly_cost_usd"])
        - float(previous["estimated_monthly_cost_usd"]),
        8,
    )
    added_detection_ids = _added_ids(previous_detections, current_detections)
    lost_detection_ids = _lost_ids(previous_detections, current_detections)
    added_question_ids = _added_ids(previous_questions, current_questions)
    lost_question_ids = _lost_ids(previous_questions, current_questions)

    return {
        "type": "transition",
        "from_configuration_id": previous["configuration_id"],
        "to_configuration_id": current["configuration_id"],
        "from_estimated_monthly_cost_usd": previous["estimated_monthly_cost_usd"],
        "to_estimated_monthly_cost_usd": current["estimated_monthly_cost_usd"],
        "from_estimated_monthly_proxy_cost_usd": previous[
            "estimated_monthly_proxy_cost_usd"
        ],
        "to_estimated_monthly_proxy_cost_usd": current[
            "estimated_monthly_proxy_cost_usd"
        ],
        "cost_estimate_kind": current["cost_estimate_kind"],
        "cost_delta_usd": cost_delta,
        "added_sources": sorted(current_sources - previous_sources),
        "removed_sources": sorted(previous_sources - current_sources),
        "added_detections": _summaries_by_id(
            detection_catalog.get("detections", []),
            added_detection_ids,
            _detection_summary,
        ),
        "lost_detections": _summaries_by_id(
            detection_catalog.get("detections", []),
            lost_detection_ids,
            _detection_summary,
        ),
        "added_investigation_questions": _summaries_by_id(
            question_catalog.get("questions", []),
            added_question_ids,
            _question_summary,
        ),
        "lost_investigation_questions": _summaries_by_id(
            question_catalog.get("questions", []),
            lost_question_ids,
            _question_summary,
        ),
        "narrative": _transition_text(
            previous,
            current,
            cost_delta,
            added_detection_ids,
            lost_detection_ids,
            added_question_ids,
            lost_question_ids,
        ),
    }


def _baseline_text(config: dict[str, Any]) -> str:
    return (
        f"Baseline: `{config['configuration_id']}` costs "
        f"${float(config['estimated_monthly_proxy_cost_usd']):.8f}/month "
        f"as `{config['cost_estimate_kind']}`, with "
        f"{config['validated_detection_count']} validated detections and "
        f"{config['investigation_question_ready_count']} investigation questions."
    )


def _transition_text(
    previous: dict[str, Any],
    current: dict[str, Any],
    cost_delta: float,
    added_detection_ids: list[str],
    lost_detection_ids: list[str],
    added_question_ids: list[str],
    lost_question_ids: list[str],
) -> str:
    return (
        f"Moving from `{previous['configuration_id']}` to "
        f"`{current['configuration_id']}` changes cost by "
        f"${cost_delta:.8f}/month as `{current['cost_estimate_kind']}`, adds detections "
        f"{_format_ids(added_detection_ids)}, loses detections "
        f"{_format_ids(lost_detection_ids)}, adds questions "
        f"{_format_ids(added_question_ids)}, and loses questions "
        f"{_format_ids(lost_question_ids)}."
    )


def _detection_summary(detection: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": detection["id"],
        "slug": detection.get("slug"),
        "title": detection["title"],
        "dependency_status": detection.get("dependency_status"),
        "validated_by_detfuzz": detection.get("dependency_status")
        == "validated_by_detfuzz",
        "required_sources": detection.get("required_sources", []),
    }


def _question_summary(question: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": question["id"],
        "question": question["question"],
        "required_sources": question.get("required_sources", []),
    }


def _added_ids(previous: dict[str, bool], current: dict[str, bool]) -> list[str]:
    return sorted(
        item_id
        for item_id, ready in current.items()
        if ready and not previous.get(item_id, False)
    )


def _lost_ids(previous: dict[str, bool], current: dict[str, bool]) -> list[str]:
    return sorted(
        item_id
        for item_id, ready in previous.items()
        if ready and not current.get(item_id, False)
    )


def _summaries_by_id(
    items: list[dict[str, Any]],
    item_ids: list[str],
    summary_fn: Any,
) -> list[dict[str, Any]]:
    selected = set(item_ids)
    return [summary_fn(item) for item in items if item["id"] in selected]


def _id_lines(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- `{item['id']}`" for item in items]


def _format_ids(item_ids: list[str]) -> str:
    if not item_ids:
        return "none"
    return ", ".join(f"`{item_id}`" for item_id in item_ids)
