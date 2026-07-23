import re
import unittest
from pathlib import Path


class NoDetFuzzImportsTests(unittest.TestCase):
    def test_signalbudget_source_does_not_import_detfuzz_code(self) -> None:
        """Enforce the deployable package boundary.

        SignalBudget is evidence-coupled to DetFuzz, not code-coupled.
        """
        root = Path(__file__).resolve().parents[1] / "src" / "signalbudget"
        offenders = _detfuzz_imports_under(root)

        self.assertEqual(offenders, [])

    def test_signalbudget_tests_do_not_import_detfuzz_code(self) -> None:
        """Keep standalone verification independent of a DetFuzz checkout."""
        project_root = Path(__file__).resolve().parents[1]
        offenders = []
        for relative_path in ("tests", "integration_tests"):
            offenders.extend(_detfuzz_imports_under(project_root / relative_path))

        self.assertEqual(offenders, [])


def _detfuzz_imports_under(root: Path) -> list[str]:
    pattern = re.compile(r"^\s*(import\s+detfuzz|from\s+detfuzz\s+import)\b")
    offenders: list[str] = []

    for path in root.rglob("*.py"):
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, start=1):
            if pattern.search(line):
                offenders.append(f"{path}:{line_number}:{line.strip()}")

    return offenders


if __name__ == "__main__":
    unittest.main()
