from __future__ import annotations

from itertools import combinations
from typing import Any

from signalbudget.costing import summarize_selected_source_costs
from signalbudget.coverage import detection_readiness, investigation_readiness

VALIDATED_DEPENDENCY_STATUS = "validated_by_detfuzz"


def enumerate_source_configurations(
    log_source_catalog: dict[str, Any],
    detection_catalog: dict[str, Any],
    question_catalog: dict[str, Any],
    source_costs: dict[str, dict[str, object]] | None = None,
    validated_rule_ids: set[str] | None = None,
) -> list[dict[str, object]]:
    source_ids = [source["id"] for source in log_source_catalog.get("sources", [])]
    configurations: list[dict[str, object]] = []

    for size in range(0, len(source_ids) + 1):
        for selected in combinations(source_ids, size):
            selected_set = set(selected)
            detections = detection_readiness(
                detection_catalog,
                selected_set,
                log_source_catalog,
            )
            questions = investigation_readiness(
                question_catalog,
                selected_set,
                log_source_catalog,
            )
            cost_summary = summarize_selected_source_costs(
                list(selected),
                source_costs or {},
            )
            validated = _validated_detection_count(
                detection_catalog,
                detections,
                validated_rule_ids or set(),
            )
            configurations.append(
                {
                    "configuration_id": _configuration_id(selected),
                    "selected_sources": list(selected),
                    "validated_detection_count": validated,
                    "telemetry_ready_detection_count": sum(detections.values()),
                    "investigation_question_ready_count": sum(questions.values()),
                    "detection_readiness": detections,
                    "investigation_readiness": questions,
                    **cost_summary,
                }
            )

    return configurations


def _configuration_id(selected: tuple[str, ...]) -> str:
    if not selected:
        return "none"
    return "+".join(selected)


def _validated_detection_count(
    detection_catalog: dict[str, Any],
    readiness: dict[str, bool],
    validated_rule_ids: set[str],
) -> int:
    count = 0
    for detection in detection_catalog.get("detections", []):
        detection_id = detection["id"]
        if (
            readiness.get(detection_id, False)
            and detection.get("dependency_status") == VALIDATED_DEPENDENCY_STATUS
            and detection_id in validated_rule_ids
        ):
            count += 1
    return count
