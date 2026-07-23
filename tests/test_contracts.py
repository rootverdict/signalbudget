import unittest
import json
from pathlib import Path

from signalbudget.contracts import (
    ContractValidationError,
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

    def test_strict_suite_contract_rejects_missing_case_evidence(self) -> None:
        payload_path = FIXTURES / "full-suite-report.json"
        payload = json.loads(payload_path.read_text(encoding="utf-8-sig"))
        payload["evidence_manifest"]["files"][0]["path"] = "B0/missing.json"
        broken_path = FIXTURES / "broken-full-suite-report.json"
        broken_path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            with self.assertRaises(ContractValidationError):
                validate_detfuzz_result_file(
                    broken_path,
                    evidence_root=FIXTURES / "evidence",
                    require_suite_contract=True,
                )
        finally:
            broken_path.unlink(missing_ok=True)

    def test_rejects_unsupported_schema_version(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_detfuzz_result_file(FIXTURES / "bad-schema-version.json")


if __name__ == "__main__":
    unittest.main()
