from __future__ import annotations

from typing import Any


def source_ids(catalog: dict[str, Any]) -> set[str]:
    return {source["id"] for source in catalog.get("sources", [])}


def detection_readiness(
    detection_catalog: dict[str, Any],
    available_sources: set[str],
    log_source_catalog: dict[str, Any] | None = None,
) -> dict[str, bool]:
    readiness: dict[str, bool] = {}
    available_fields = fields_available_from_sources(log_source_catalog, available_sources)
    for detection in detection_catalog.get("detections", []):
        required = set(detection.get("required_sources", []))
        required_fields = set(detection.get("required_fields", []))
        fields_ready = (
            True
            if log_source_catalog is None
            else required_fields.issubset(available_fields)
        )
        readiness[detection["id"]] = required.issubset(
            available_sources
        ) and fields_ready
    return readiness


def investigation_readiness(
    question_catalog: dict[str, Any],
    available_sources: set[str],
    log_source_catalog: dict[str, Any] | None = None,
) -> dict[str, bool]:
    readiness: dict[str, bool] = {}
    available_fields = fields_available_from_sources(log_source_catalog, available_sources)
    for question in question_catalog.get("questions", []):
        required = set(question.get("required_sources", []))
        required_fields = set(question.get("required_fields", []))
        fields_ready = (
            True
            if log_source_catalog is None
            else required_fields.issubset(available_fields)
        )
        readiness[question["id"]] = required.issubset(
            available_sources
        ) and fields_ready
    return readiness


def fields_available_from_sources(
    log_source_catalog: dict[str, Any] | None,
    available_sources: set[str],
) -> set[str]:
    if log_source_catalog is None:
        return set()
    fields: set[str] = set()
    for source in log_source_catalog.get("sources", []):
        if source["id"] in available_sources:
            fields.update(source.get("required_fields", []))
    return fields


def classification_counts(detfuzz_summary: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in detfuzz_summary["cases"]:
        classification = case["classification"]
        counts[classification] = counts.get(classification, 0) + 1
    return counts
