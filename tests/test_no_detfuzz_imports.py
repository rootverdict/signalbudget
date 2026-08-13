import importlib
import pkgutil
import re
import sys
import unittest
from pathlib import Path

# Matches every static import form that would couple this package to DetFuzz:
#   import detfuzz
#   import detfuzz.suite
#   from detfuzz import contract
#   from detfuzz.contract import validate_report
# The optional dotted-suffix group is what catches submodule imports; an earlier
# version of this pattern required "from detfuzz import" literally and so let
# "from detfuzz.contract import ..." through. The trailing \b keeps unrelated
# distributions such as "detfuzzy" from matching.
_DETFUZZ_IMPORT = re.compile(r"^\s*(?:import|from)\s+detfuzz(?:\.[\w.]+)?\b")


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

    def test_importing_every_signalbudget_module_does_not_load_detfuzz(self) -> None:
        """Cover the dynamic imports a source scan cannot see.

        importlib.import_module("detfuzz") and __import__ calls are invisible to
        the regex above, so the boundary is also asserted against the interpreter
        state after every submodule has actually been imported.
        """
        import signalbudget

        for module in pkgutil.walk_packages(
            signalbudget.__path__, prefix="signalbudget."
        ):
            importlib.import_module(module.name)

        loaded = sorted(
            name
            for name in sys.modules
            if name == "detfuzz" or name.startswith("detfuzz.")
        )

        self.assertEqual(loaded, [])

    def test_guard_detects_a_submodule_import(self) -> None:
        """The guard must fail on planted violations, or it proves nothing.

        A scanner that never fires is indistinguishable from one that is broken,
        which is the same reasoning as DetFuzz's NC1 negative control.
        """
        for planted in (
            "import detfuzz",
            "import detfuzz.suite",
            "from detfuzz import contract",
            "from detfuzz.contract import validate_report",
            "    from detfuzz.models import Classification",
        ):
            with self.subTest(planted=planted):
                self.assertTrue(_DETFUZZ_IMPORT.search(planted))

        for allowed in (
            "from detfuzzy import unrelated",
            "import detfuzzical",
            "# SignalBudget must not import detfuzz.* code.",
        ):
            with self.subTest(allowed=allowed):
                self.assertIsNone(_DETFUZZ_IMPORT.search(allowed))


def _detfuzz_imports_under(root: Path) -> list[str]:
    offenders: list[str] = []

    for path in root.rglob("*.py"):
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, start=1):
            if _DETFUZZ_IMPORT.search(line):
                offenders.append(f"{path}:{line_number}:{line.strip()}")

    return offenders


if __name__ == "__main__":
    unittest.main()
