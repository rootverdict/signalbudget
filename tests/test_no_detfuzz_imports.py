import re
import unittest
from pathlib import Path


class NoDetFuzzImportsTests(unittest.TestCase):
    def test_signalbudget_source_does_not_import_detfuzz_code(self) -> None:
        """Enforce the deployable package boundary.

        This intentionally scans only src/signalbudget. The repository-level
        integration_tests/ directory is an explicit exception because it
        verifies cross-package compatibility and is not shipped as part of the
        SignalBudget package.
        """
        root = Path(__file__).resolve().parents[1] / "src" / "signalbudget"
        pattern = re.compile(r"^\s*(import\s+detfuzz|from\s+detfuzz\s+import)\b")
        offenders: list[str] = []

        for path in root.rglob("*.py"):
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if pattern.search(line):
                    offenders.append(f"{path}:{line_number}:{line.strip()}")

        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
