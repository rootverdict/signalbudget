from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path, PurePosixPath
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
CONTRACT_SCHEMA_FILE = (
    Path(__file__).resolve().parent
    / "data"
    / "contracts"
    / "detfuzz_result_schema.json"
)


class ContractValidationError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ContractValidationError("DetFuzz result must be a JSON object")
    return payload


@lru_cache(maxsize=1)
def load_contract_schema() -> dict[str, Any]:
    schema = json.loads(CONTRACT_SCHEMA_FILE.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ContractValidationError("DetFuzz contract schema must be a JSON object")
    return schema


def validate_detfuzz_result(
    payload: dict[str, Any],
    evidence_root: Path | None = None,
    require_suite_contract: bool = False,
) -> dict[str, Any]:
    _validate_schema_value(payload, load_contract_schema(), "result")
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
        manifest_result = _validate_evidence_manifest(
            payload,
            evidence_root,
            cases=normalized_cases,
        )
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
        if not isinstance(case.get("detection_matched"), bool):
            raise ContractValidationError(f"{case_id} detection_matched must be boolean")
        classification = case["classification"]
        if classification == "DETECTED" and case["detection_matched"] is not True:
            raise ContractValidationError(
                f"{case_id} classified as DETECTED must have detection_matched true"
            )
        if classification == "VALID_BYPASS" and case["detection_matched"] is not False:
            raise ContractValidationError(
                f"{case_id} classified as VALID_BYPASS must have detection_matched false"
            )


def _validate_evidence_manifest(
    payload: dict[str, Any],
    evidence_root: Path | None,
    cases: list[dict[str, Any]] | None = None,
) -> dict[str, object]:
    manifest = payload.get("evidence_manifest")
    if not isinstance(manifest, dict):
        raise ContractValidationError("DetFuzz report must include evidence_manifest")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ContractValidationError("evidence_manifest.files must be non-empty")

    if evidence_root is None:
        raise ContractValidationError(
            "evidence_root is required for strict verification; "
            "the manifest root is informational and is never trusted"
        )
    root = evidence_root.resolve()
    if not root.is_dir():
        raise ContractValidationError(f"evidence root does not exist: {root}")
    manifest_paths: set[str] = set()
    resolved_paths: dict[str, Path] = {}
    checked = 0
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            raise ContractValidationError(f"evidence_manifest.files[{index}] must be object")
        _require(item, "path", str, prefix=f"evidence_manifest.files[{index}]")
        _require(item, "sha256", str, prefix=f"evidence_manifest.files[{index}]")
        _require(item, "size_bytes", int, prefix=f"evidence_manifest.files[{index}]")
        normalized_path = _normalize_evidence_path(item["path"])
        if normalized_path in manifest_paths:
            raise ContractValidationError(
                f"duplicate evidence manifest path: {item['path']}"
            )
        manifest_paths.add(normalized_path)
        _validate_manifest_metadata(item, index)
        file_path = _resolve_evidence_path(root, item["path"])
        if not file_path.is_file():
            raise ContractValidationError(
                f"evidence manifest file is missing: {item['path']}"
            )
        digest, size = _hash_file(file_path)
        if digest.lower() != item["sha256"].lower():
            raise ContractValidationError(
                f"evidence hash mismatch for {item['path']}"
            )
        if size != int(item["size_bytes"]):
            raise ContractValidationError(
                f"evidence size mismatch for {item['path']}"
            )
        checked += 1
        resolved_paths[normalized_path] = file_path
    _require_complete_case_evidence(manifest_paths)
    if cases is not None:
        _validate_case_evidence(cases, resolved_paths)
    return {
        "evidence_manifest_file_count": len(files),
        "evidence_hashes_verified": checked == len(files),
        "evidence_files_checked": checked,
    }


def _hash_file(path: Path, chunk_size: int = 1024 * 1024) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _validate_case_evidence(
    cases: list[dict[str, Any]],
    resolved_paths: dict[str, Path],
) -> None:
    for case in cases:
        case_id = str(case["case_id"])
        case_record = _load_case_evidence(
            case_id,
            "case-record.json",
            resolved_paths,
        )
        for field in (
            "case_id",
            "classification",
            "marker_valid",
            "telemetry_valid",
            "executable_identity_valid",
            "detection_matched",
            "rule_id",
        ):
            if field not in case_record:
                raise ContractValidationError(
                    f"{case_id} case-record.json missing required field: {field}"
                )
            if case_record[field] != case[field]:
                raise ContractValidationError(
                    f"{case_id} {field} does not match case-record.json"
                )

        evidence_flags = (
            ("marker-validation.json", "marker_valid"),
            ("telemetry-validation.json", "telemetry_valid"),
            ("executable-identity.json", "executable_identity_valid"),
        )
        for file_name, case_field in evidence_flags:
            evidence = _load_case_evidence(case_id, file_name, resolved_paths)
            valid = evidence.get("valid")
            if not isinstance(valid, bool):
                raise ContractValidationError(
                    f"{case_id} {file_name} valid must be boolean"
                )
            if valid is not case[case_field]:
                raise ContractValidationError(
                    f"{case_id} {case_field} does not match {file_name}"
                )

        detection = _load_case_evidence(
            case_id,
            "detection-result.json",
            resolved_paths,
        )
        matched = detection.get("matched")
        if not isinstance(matched, bool):
            raise ContractValidationError(
                f"{case_id} detection-result.json matched must be boolean"
            )
        if matched is not case["detection_matched"]:
            raise ContractValidationError(
                f"{case_id} detection_matched does not match detection-result.json"
            )
        if detection.get("rule_id") != EXPECTED_RULE_ID:
            raise ContractValidationError(
                f"{case_id} detection-result.json rule_id must be {EXPECTED_RULE_ID}"
            )


def _load_case_evidence(
    case_id: str,
    file_name: str,
    resolved_paths: dict[str, Path],
) -> dict[str, Any]:
    normalized_path = _normalize_evidence_path(f"{case_id}/{file_name}")
    return load_json(resolved_paths[normalized_path])


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


def _resolve_evidence_path(root: Path, value: str) -> Path:
    normalized = value.replace("\\", "/")
    pure_path = PurePosixPath(normalized)
    has_windows_drive = len(normalized) >= 2 and normalized[1] == ":"
    if (
        not normalized
        or pure_path.is_absolute()
        or has_windows_drive
        or ".." in pure_path.parts
    ):
        raise ContractValidationError(
            f"evidence path must be safe and relative: {value}"
        )
    resolved = (root / Path(*pure_path.parts)).resolve()
    if not resolved.is_relative_to(root):
        raise ContractValidationError(
            f"evidence path must remain within evidence root: {value}"
        )
    return resolved


def _validate_manifest_metadata(item: dict[str, Any], index: int) -> None:
    sha256 = item["sha256"]
    if (
        len(sha256) != 64
        or any(character not in "0123456789abcdefABCDEF" for character in sha256)
    ):
        raise ContractValidationError(
            f"evidence_manifest.files[{index}].sha256 must be 64 hexadecimal characters"
        )
    size = item["size_bytes"]
    if isinstance(size, bool) or size < 0:
        raise ContractValidationError(
            f"evidence_manifest.files[{index}].size_bytes must be non-negative"
        )


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


def _validate_schema_value(value: Any, schema: dict[str, Any], path: str) -> None:
    if "const" in schema and value != schema["const"]:
        raise ContractValidationError(f"{path} must equal {schema['const']!r}")

    expected_types = schema.get("type")
    if expected_types is not None:
        allowed = (
            expected_types if isinstance(expected_types, list) else [expected_types]
        )
        if not any(_matches_schema_type(value, item) for item in allowed):
            allowed_text = " or ".join(str(item) for item in allowed)
            raise ContractValidationError(f"{path} must be {allowed_text}")

    if isinstance(value, str) and "minLength" in schema:
        if len(value) < int(schema["minLength"]):
            raise ContractValidationError(
                f"{path} must contain at least {schema['minLength']} character(s)"
            )

    if isinstance(value, list):
        if "minItems" in schema and len(value) < int(schema["minItems"]):
            raise ContractValidationError(
                f"{path} must contain at least {schema['minItems']} item(s)"
            )
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema_value(item, item_schema, f"{path}[{index}]")

    if not isinstance(value, dict):
        return

    for key in schema.get("required", []):
        if key not in value:
            raise ContractValidationError(f"{path} missing required field: {key}")

    properties = schema.get("properties", {})
    for key, item in value.items():
        item_schema = properties.get(key)
        if isinstance(item_schema, dict):
            _validate_schema_value(item, item_schema, f"{path}.{key}")
            continue
        additional = schema.get("additionalProperties", True)
        if additional is False:
            raise ContractValidationError(f"{path} has unsupported field: {key}")
        if isinstance(additional, dict):
            _validate_schema_value(item, additional, f"{path}.{key}")


def _matches_schema_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ContractValidationError(f"unsupported contract schema type: {expected}")
