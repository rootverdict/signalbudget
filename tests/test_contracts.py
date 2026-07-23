import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from signalbudget.contracts import (
    ContractValidationError,
    _validate_evidence_manifest,
    validate_detfuzz_result,
    validate_detfuzz_result_file,
)
from signalbudget.coverage import classification_counts

FIXTURES = Path(__file__).parent / "fixtures"


class ContractTests(unittest.TestCase):
    def test_validates_real_phase7_benign_result_shape(self) -> None:
        summary = validate_detfuzz_result_file(FIXTURES / "benign-results.json")

        self.assertEqual(summary["schema_version"], "1.0")
        self.assertEqual(summary["suite_id"], "1a545575-f640-45b2-91de-fc0bf1ed419c")
        self.assertEqual(classification_counts(summary)["BENIGN_ALERT"], 2)

    def test_validates_real_phase6_b0_report_shape(self) -> None:
        summary = validate_detfuzz_result_file(
            FIXTURES / "phase6-b0-suite-report.json"
        )

        self.assertEqual(summary["cases"][0]["case_id"], "B0")
        self.assertEqual(summary["cases"][0]["classification"], "DETECTED")

    def test_strict_suite_contract_verifies_full_suite_and_hashes(self) -> None:
        summary = validate_detfuzz_result_file(
            FIXTURES / "full-suite-report.json",
            evidence_root=FIXTURES / "evidence",
            require_suite_contract=True,
        )

        self.assertEqual(
            summary["validated_rule_ids"],
            ["d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62"],
        )
        self.assertTrue(summary["evidence_hashes_verified"])

    def test_strict_suite_contract_rejects_partial_report(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_detfuzz_result_file(
                FIXTURES / "phase6-b0-suite-report.json",
                require_suite_contract=True,
            )

    def test_strict_suite_contract_rejects_detected_case_without_match(self) -> None:
        payload = json.loads(
            (FIXTURES / "full-suite-report.json").read_text(encoding="utf-8-sig")
        )
        payload["cases"][0]["detection_matched"] = False

        with self.assertRaisesRegex(
            ContractValidationError,
            "classified as DETECTED must have detection_matched true",
        ):
            validate_detfuzz_result(
                payload,
                evidence_root=FIXTURES / "evidence",
                require_suite_contract=True,
            )

    def test_strict_suite_contract_cross_checks_detection_evidence(self) -> None:
        payload = json.loads(
            (FIXTURES / "full-suite-report.json").read_text(encoding="utf-8-sig")
        )
        with tempfile.TemporaryDirectory() as directory:
            evidence_root = Path(directory) / "evidence"
            shutil.copytree(FIXTURES / "evidence", evidence_root)
            detection_path = evidence_root / "B0" / "detection-result.json"
            detection = json.loads(detection_path.read_text(encoding="utf-8-sig"))
            detection["matched"] = False
            detection_path.write_text(json.dumps(detection), encoding="utf-8")
            manifest_item = next(
                item
                for item in payload["evidence_manifest"]["files"]
                if item["path"].replace("\\", "/").lower()
                == "b0/detection-result.json"
            )
            data = detection_path.read_bytes()
            manifest_item["sha256"] = hashlib.sha256(data).hexdigest()
            manifest_item["size_bytes"] = len(data)

            with self.assertRaisesRegex(
                ContractValidationError,
                "does not match detection-result.json",
            ):
                validate_detfuzz_result(
                    payload,
                    evidence_root=evidence_root,
                    require_suite_contract=True,
                )

    def test_strict_suite_contract_cross_checks_health_evidence(self) -> None:
        payload = json.loads(
            (FIXTURES / "full-suite-report.json").read_text(encoding="utf-8-sig")
        )
        with tempfile.TemporaryDirectory() as directory:
            evidence_root = Path(directory) / "evidence"
            shutil.copytree(FIXTURES / "evidence", evidence_root)
            marker_path = evidence_root / "B0" / "marker-validation.json"
            marker = json.loads(marker_path.read_text(encoding="utf-8-sig"))
            marker["valid"] = False
            marker_path.write_text(json.dumps(marker), encoding="utf-8")
            _update_manifest_item(payload, "B0/marker-validation.json", marker_path)

            with self.assertRaisesRegex(
                ContractValidationError,
                "marker_valid does not match marker-validation.json",
            ):
                validate_detfuzz_result(
                    payload,
                    evidence_root=evidence_root,
                    require_suite_contract=True,
                )

    def test_strict_suite_contract_cross_checks_case_record(self) -> None:
        payload = json.loads(
            (FIXTURES / "full-suite-report.json").read_text(encoding="utf-8-sig")
        )
        with tempfile.TemporaryDirectory() as directory:
            evidence_root = Path(directory) / "evidence"
            shutil.copytree(FIXTURES / "evidence", evidence_root)
            record_path = evidence_root / "B0" / "case-record.json"
            record = json.loads(record_path.read_text(encoding="utf-8-sig"))
            record["classification"] = "VALID_BYPASS"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            _update_manifest_item(payload, "B0/case-record.json", record_path)

            with self.assertRaisesRegex(
                ContractValidationError,
                "classification does not match case-record.json",
            ):
                validate_detfuzz_result(
                    payload,
                    evidence_root=evidence_root,
                    require_suite_contract=True,
                )

    def test_strict_suite_contract_accepts_legacy_preliminary_bypass_record(
        self,
    ) -> None:
        payload = json.loads(
            (FIXTURES / "full-suite-report.json").read_text(encoding="utf-8-sig")
        )
        with tempfile.TemporaryDirectory() as directory:
            evidence_root = Path(directory) / "evidence"
            shutil.copytree(FIXTURES / "evidence", evidence_root)
            record_path = evidence_root / "M1" / "case-record.json"
            record = json.loads(record_path.read_text(encoding="utf-8-sig"))
            record["classification"] = "CANDIDATE_VALID_BYPASS"
            record["preliminary_classification"] = "CANDIDATE_VALID_BYPASS"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            _update_manifest_item(payload, "M1/case-record.json", record_path)

            summary = validate_detfuzz_result(
                payload,
                evidence_root=evidence_root,
                require_suite_contract=True,
            )

        self.assertEqual(
            summary["legacy_preliminary_classifications_accepted"],
            ["M1"],
        )

    def test_strict_suite_contract_rejects_unmarked_preliminary_bypass_record(
        self,
    ) -> None:
        payload = json.loads(
            (FIXTURES / "full-suite-report.json").read_text(encoding="utf-8-sig")
        )
        with tempfile.TemporaryDirectory() as directory:
            evidence_root = Path(directory) / "evidence"
            shutil.copytree(FIXTURES / "evidence", evidence_root)
            record_path = evidence_root / "M1" / "case-record.json"
            record = json.loads(record_path.read_text(encoding="utf-8-sig"))
            record["classification"] = "CANDIDATE_VALID_BYPASS"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            _update_manifest_item(payload, "M1/case-record.json", record_path)

            with self.assertRaisesRegex(
                ContractValidationError,
                "classification does not match case-record.json",
            ):
                validate_detfuzz_result(
                    payload,
                    evidence_root=evidence_root,
                    require_suite_contract=True,
                )

    def test_strict_suite_contract_rejects_missing_case_evidence(self) -> None:
        payload_path = FIXTURES / "full-suite-report.json"
        payload = json.loads(payload_path.read_text(encoding="utf-8-sig"))
        payload["evidence_manifest"]["files"][0]["path"] = "B0/missing.json"
        with tempfile.TemporaryDirectory() as directory:
            broken_path = Path(directory) / "broken-full-suite-report.json"
            broken_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaises(ContractValidationError):
                validate_detfuzz_result_file(
                    broken_path,
                    evidence_root=FIXTURES / "evidence",
                    require_suite_contract=True,
                )

    def test_rejects_unsupported_schema_version(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_detfuzz_result_file(FIXTURES / "bad-schema-version.json")

    def test_runtime_schema_rejects_invalid_optional_field_type(self) -> None:
        payload = {
            "schema_version": "1.0",
            "suite_id": "schema-test",
            "environment": "not-an-object",
            "cases": [{"case_id": "B0", "classification": "DETECTED"}],
        }

        with self.assertRaisesRegex(
            ContractValidationError,
            "result.environment must be object",
        ):
            validate_detfuzz_result(payload)

    def test_manifest_rejects_paths_outside_evidence_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            evidence_root = workspace / "evidence"
            evidence_root.mkdir()
            outside = workspace / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            payload = {
                "evidence_manifest": {
                    "root": str(evidence_root),
                    "files": [
                        {
                            "path": "../outside.txt",
                            "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                            "size_bytes": outside.stat().st_size,
                        }
                    ],
                }
            }

            with self.assertRaisesRegex(
                ContractValidationError,
                "safe and relative",
            ):
                _validate_evidence_manifest(payload, evidence_root)

    def test_strict_verification_requires_an_explicit_evidence_root(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "evidence_root is required"):
            validate_detfuzz_result_file(
                FIXTURES / "full-suite-report.json",
                require_suite_contract=True,
            )

    def test_manifest_rejects_invalid_sha256_metadata(self) -> None:
        payload = {
            "evidence_manifest": {
                "root": "ignored",
                "files": [
                    {
                        "path": "B0/case-record.json",
                        "sha256": "not-a-sha256",
                        "size_bytes": 1,
                    }
                ],
            }
        }

        with self.assertRaisesRegex(ContractValidationError, "64 hexadecimal"):
            _validate_evidence_manifest(payload, FIXTURES / "evidence")

    def test_manifest_hashing_does_not_read_entire_files_at_once(self) -> None:
        payload = json.loads(
            (FIXTURES / "full-suite-report.json").read_text(encoding="utf-8-sig")
        )

        with patch.object(
            Path,
            "read_bytes",
            side_effect=AssertionError("read_bytes must not be used for evidence"),
        ):
            result = _validate_evidence_manifest(payload, FIXTURES / "evidence")

        self.assertTrue(result["evidence_hashes_verified"])


def _update_manifest_item(
    payload: dict[str, object],
    relative_path: str,
    evidence_path: Path,
) -> None:
    manifest = payload["evidence_manifest"]
    assert isinstance(manifest, dict)
    files = manifest["files"]
    assert isinstance(files, list)
    manifest_item = next(
        item
        for item in files
        if isinstance(item, dict)
        and str(item["path"]).replace("\\", "/").lower() == relative_path.lower()
    )
    data = evidence_path.read_bytes()
    manifest_item["sha256"] = hashlib.sha256(data).hexdigest()
    manifest_item["size_bytes"] = len(data)


if __name__ == "__main__":
    unittest.main()
