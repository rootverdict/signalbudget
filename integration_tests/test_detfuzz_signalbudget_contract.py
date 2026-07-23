import json
import tempfile
import unittest
from pathlib import Path

from detfuzz.report import write_report_bundle
from signalbudget.contracts import validate_detfuzz_result_file


EXPECTED_RULE_ID = "d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62"
EXPECTED_RULE_SLUG = "detfuzz-v0-powershell-encoded-command"
CASE_IDS = ("B0", "M1", "M2", "M3", "M4", "M5", "NC1", "B1")


class DetFuzzSignalBudgetIntegrationTests(unittest.TestCase):
    def test_detfuzz_report_bundle_is_accepted_by_signalbudget_strict_contract(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root)
            evidence_root = workspace / "evidence"
            evidence_root.mkdir()
            cases = []
            for case_id in CASE_IDS:
                classification = _classification_for(case_id)
                matched = case_id not in {"M1", "NC1"}
                cases.append(
                    {
                        "case_id": case_id,
                        "classification": classification,
                        "marker_valid": True,
                        "telemetry_valid": True,
                        "executable_identity_valid": True,
                        "detection_matched": matched,
                        "rule_id": EXPECTED_RULE_ID,
                        "rule_slug": EXPECTED_RULE_SLUG,
                    }
                )
                _write_case_evidence(evidence_root / case_id, case_id, matched)

            suite_results_path = workspace / "suite-results.json"
            suite_results_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "suite_id": "integration-suite",
                        "suite_status": "COMPLETED",
                        "abort_reason": None,
                        "environment": {
                            "rule_id": EXPECTED_RULE_ID,
                            "rule_slug": EXPECTED_RULE_SLUG,
                        },
                        "cases": cases,
                    }
                ),
                encoding="utf-8",
            )

            report_paths = write_report_bundle(
                suite_results_path,
                evidence_root,
                workspace / "reports",
            )
            summary = validate_detfuzz_result_file(
                report_paths["json_report"],
                evidence_root=evidence_root,
                require_suite_contract=True,
            )

            self.assertEqual(summary["suite_status"], "COMPLETED")
            self.assertTrue(summary["evidence_hashes_verified"])
            self.assertEqual(summary["validated_rule_ids"], [EXPECTED_RULE_ID])


def _write_case_evidence(case_dir: Path, case_id: str, detection_matched: bool) -> None:
    case_dir.mkdir()
    files = {
        "case-record.json": {"case_id": case_id},
        "execution.json": {"case_id": case_id, "exit_code": 0},
        "marker-validation.json": {"valid": True},
        "telemetry-validation.json": {"valid": True},
        "executable-identity.json": {"valid": True},
        "detection-result.json": {
            "rule_id": EXPECTED_RULE_ID,
            "rule_slug": EXPECTED_RULE_SLUG,
            "matched": detection_matched,
        },
    }
    for file_name, payload in files.items():
        (case_dir / file_name).write_text(json.dumps(payload), encoding="utf-8")
    (case_dir / "matched-sysmon-event.xml").write_text("<Event />", encoding="utf-8")
    if case_id != "NC1":
        (case_dir / "effect.json").write_text(
            json.dumps({"case_id": case_id, "result": "completed"}),
            encoding="utf-8",
        )


def _classification_for(case_id: str) -> str:
    if case_id == "M1":
        return "VALID_BYPASS"
    if case_id == "NC1":
        return "INVALID_MUTANT"
    return "DETECTED"


if __name__ == "__main__":
    unittest.main()
