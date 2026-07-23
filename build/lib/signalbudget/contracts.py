from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any


SUPPORTED_DETFUZZ_SCHEMA_VERSION = "1.0"
EXPECTED_SUITE_CASE_IDS = {"B0", "M1", "M2", "M3", "M4", "M5", "NC1", "B1"}
MUTATION_CASE_IDS = {"M1", "M2", "M3", "M4", "M5"}
ALLOWED_MUTATION_CLASSIFICATIONS = {"DETECTED", "VALID_BYPASS"}
EXPECTED_RULE_ID = "d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62"
REQUIRED_CASE_EVIDENCE_FILES = (
    "case-record.json",
    "execution.json",
    "marker-validation.json",
    "telemetry-validation.json",
    "executable-identity.json",
    "detection-result.json",
    "matched-sysmon-event.xml",
)


class ContractValidationError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ContractValidationError("DetFuzz result must be a JSON object")
    return payload


def validate_detfuzz_result(
    payload: dict[str, Any],
    evidence_root: Path | None = None,
    require_suite_contract: bool = False,
) -> dict[str, Any]:
    _require(payload, "schema_version", str)
    if payload["schema_version"] != SUPPORTED_DETFUZZ_SCHEMA_VERSION:
        raise ContractValidationError(
            f"unsupported DetFuzz schema_version: {payload['schema_version']}"
        )
    _require(payload, "suite_id", str)
    _require(payload, "cases", list)
    if not payload["cases"]:
        raise ContractValidationError("DetFuzz result must include at least one case")

    normalized_cases = []
    for index, case in enumerate(payload["cases"]):
        if not isinstance(case, dict):
            raise ContractValidationError(f"case {index} must be an object")
        _require(case, "case_id", str, prefix=f"case {index}")
        _require(case, "classification", str, prefix=f"case {index}")
        normalized_cases.append(
            {
                "case_id": case["case_id"],
                "classification": case["classification"],
                "telemetry_valid": case.get("telemetry_valid"),
                "detection_matched": case.get("detection_matched"),
                "marker_valid": case.get("marker_valid"),
                "executable_identity_valid": case.get("executable_identity_valid"),
                "rule_id": case.get("rule_id"),
                "rule_slug": case.get("rule_slug"),
            }
        )

    summary = {
        "schema_version": payload["schema_version"],
        "suite_id": payload["suite_id"],
        "suite_status": payload.get("suite_status"),
        "rule_id": payload.get("environment", {}).get("rule_id"),
        "rule_slug": payload.get("environment", {}).get("rule_slug"),
        "telemetry": payload.get("environment", {}).get("telemetry"),
        "cases": normalized_cases,
    }
    if require_suite_contract:
        _validate_analysis_contract(payload, normalized_cases)
        manifest_result = _validate_evidence_manifest(payload, evidence_root)
        summary.update(manifest_result)
        summary["validated_rule_ids"] = [EXPECTED_RULE_ID]
    else:
        summary["validated_rule_ids"] = []
    return summary


def validate_detfuzz_result_file(
    path: Path,
    evidence_root: Path | None = None,
    require_suite_contract: bool = False,
) -> dict[str, Any]:
    return validate_detfuzz_result(
        load_json(path),
        evidence_root=evidence_root,
        require_suite_contract=require_suite_contract,
    )


def _validate_analysis_contract(
    payload: dict[str, Any],
    cases: list[dict[str, Any]],
) -> None:
    if payload.get("suite_status") != "COMPLETED":
        raise ContractValidationError("DetFuzz suite_status must be COMPLETED")
    rule_id = payload.get("environment", {}).get("rule_id")
    if rule_id != EXPECTED_RULE_ID:
        raise ContractValidationError(f"DetFuzz rule_id must be {EXPECTED_RULE_ID}")
    by_id = {case["case_id"]: case for case in cases}
    case_ids = [case["case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ContractValidationError("DetFuzz suite case IDs must be unique")
    missing = EXPECTED_SUITE_CASE_IDS - set(case_ids)
    extra = set(case_ids) - EXPECTED_SUITE_CASE_IDS
    if missing or extra or len(case_ids) != len(EXPECTED_SUITE_CASE_IDS):
        raise ContractValidationError(
            "DetFuzz suite must contain exactly these cases: "
            + ", ".join(sorted(EXPECTED_SUITE_CASE_IDS))
        )
    if by_id["B0"]["classification"] != "DETECTED":
        raise ContractValidationError("opening baseline B0 must be DETECTED")
    if by_id["B1"]["classification"] != "DETECTED":
        raise ContractValidationError("closing baseline B1 must be DETECTED")
    if by_id["NC1"]["classification"] != "INVALID_MUTANT":
        raise ContractValidationError("negative control NC1 must be INVALID_MUTANT")
    for case_id in MUTATION_CASE_IDS:
        if by_id[case_id]["classification"] not in ALLOWED_MUTATION_CLASSIFICATIONS:
            raise ContractValidationError(
                f"{case_id} classification must be DETECTED or VALID_BYPASS"
            )
    for case_id, case in by_id.items():
        if case.get("marker_valid") is not True:
            raise ContractValidationError(f"{case_id} marker_valid must be true")
        if case.get("telemetry_valid") is not True:
            raise ContractValidationError(f"{case_id} telemetry_valid must be true")
        if case.get("executable_identity_valid") is not True:
            raise ContractValidationError(
                f"{case_id} executable_identity_valid must be true"
            )
        if case.get("rule_id") != EXPECTED_RULE_ID:
            raise ContractValidationError(f"{case_id} rule_id must be {EXPECTED_RULE_ID}")
        if case_id != "NC1" and not isinstance(case.get("detection_matched"), bool):
            raise ContractValidationError(f"{case_id} detection_matched must be boolean")


def _validate_evidence_manifest(
    payload: dict[str, Any],
    evidence_root: Path | None,
) -> dict[str, object]:
    manifest = payload.get("evidence_manifest")
    if not isinstance(manifest, dict):
        raise ContractValidationError("DetFuzz report must include evidence_manifest")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ContractValidationError("evidence_manifest.files must be non-empty")

    root = evidence_root or Path(str(manifest.get("root", "")))
    manifest_paths: set[str] = set()
    checked = 0
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            raise ContractValidationError(f"evidence_manifest.files[{index}] must be object")
        _require(item, "path", str, prefix=f"evidence_manifest.files[{index}]")
        _require(item, "sha256", str, prefix=f"evidence_manifest.files[{index}]")
        _require(item, "size_bytes", int, prefix=f"evidence_manifest.files[{index}]")
        manifest_paths.add(_normalize_evidence_path(item["path"]))
        file_path = root / item["path"]
        if file_path.exists():
            data = file_path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if digest.lower() != item["sha256"].lower():
                raise ContractValidationError(
                    f"evidence hash mismatch for {item['path']}"
                )
            if len(data) != int(item["size_bytes"]):
                raise ContractValidationError(
                    f"evidence size mismatch for {item['path']}"
                )
            checked += 1
    if checked != len(files):
        raise ContractValidationError(
            "all evidence manifest files must be present for hash verification"
        )
    _require_complete_case_evidence(manifest_paths)
    return {
        "evidence_manifest_file_count": len(files),
        "evidence_hashes_verified": checked == len(files),
        "evidence_files_checked": checked,
    }


def _require_complete_case_evidence(manifest_paths: set[str]) -> None:
    required: set[str] = set()
    for case_id in EXPECTED_SUITE_CASE_IDS:
        required.update(
            _normalize_evidence_path(f"{case_id}/{file_name}")
            for file_name in REQUIRED_CASE_EVIDENCE_FILES
        )
        if case_id != "NC1":
            required.add(_normalize_evidence_path(f"{case_id}/effect.json"))
    missing = sorted(required - manifest_paths)
    if missing:
        raise ContractValidationError(
            "evidence_manifest missing required per-case evidence: "
            + ", ".join(missing)
        )


def _normalize_evidence_path(path: str) -> str:
    return path.replace("\\", "/").lower()


def _require(
    payload: dict[str, Any],
    key: str,
    expected_type: type,
    prefix: str = "result",
) -> None:
    if key not in payload:
        raise ContractValidationError(f"{prefix} missing required field: {key}")
    if not isinstance(payload[key], expected_type):
        raise ContractValidationError(
            f"{prefix}.{key} must be {expected_type.__name__}"
        )
