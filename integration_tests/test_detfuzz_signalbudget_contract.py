import unittest
from pathlib import Path

from signalbudget.contracts import validate_detfuzz_result_file

EXPECTED_RULE_ID = "d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62"
FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


class DetFuzzSignalBudgetIntegrationTests(unittest.TestCase):
    def test_exported_detfuzz_evidence_is_accepted_by_strict_contract(self) -> None:
        """SignalBudget consumes DetFuzz evidence artifacts, not DetFuzz code."""
        summary = validate_detfuzz_result_file(
            FIXTURES / "full-suite-report.json",
            evidence_root=FIXTURES / "evidence",
            require_suite_contract=True,
        )

        self.assertEqual(summary["suite_status"], "COMPLETED")
        self.assertTrue(summary["evidence_hashes_verified"])
        self.assertEqual(summary["evidence_files_checked"], 63)
        self.assertEqual(summary["validated_rule_ids"], [EXPECTED_RULE_ID])


if __name__ == "__main__":
    unittest.main()
