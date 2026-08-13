import hashlib
import re
import unittest
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DOCUMENT = PROJECT_ROOT / "docs" / "phase-11-vm-validation.md"
EVIDENCE_ARCHIVE = (
    PROJECT_ROOT
    / "evidence"
    / "detfuzz-signalbudget-results-20260723-212216-posix.zip"
)


class ReleaseMetadataTests(unittest.TestCase):
    def test_documented_evidence_archive_metadata_matches_archive(self) -> None:
        document = VALIDATION_DOCUMENT.read_text(encoding="utf-8")
        expected_digest = _documented_sha256(document, EVIDENCE_ARCHIVE.relative_to(PROJECT_ROOT))
        expected_entries = _documented_integer(document, r"entries: (\d+) total")
        expected_files = _documented_integer(document, r"\((\d+) files")
        expected_directories = _documented_integer(document, r"files, (\d+) directories\)")
        expected_bytes = _documented_integer(document, r"uncompressed bytes: (\d+)")
        expected_unsafe = _documented_integer(document, r"unsafe archive paths: (\d+)")

        self.assertEqual(_sha256(EVIDENCE_ARCHIVE), expected_digest)
        with ZipFile(EVIDENCE_ARCHIVE) as archive:
            entries = archive.infolist()
            file_count = sum(not entry.is_dir() for entry in entries)
            directory_count = sum(entry.is_dir() for entry in entries)
            uncompressed_bytes = sum(entry.file_size for entry in entries)
            unsafe_count = sum(_is_unsafe_archive_path(entry.filename) for entry in entries)

        self.assertEqual(len(entries), expected_entries)
        self.assertEqual(file_count, expected_files)
        self.assertEqual(directory_count, expected_directories)
        self.assertEqual(uncompressed_bytes, expected_bytes)
        self.assertEqual(unsafe_count, expected_unsafe)

    def test_documented_report_hashes_match_committed_reports(self) -> None:
        document = VALIDATION_DOCUMENT.read_text(encoding="utf-8")
        report_paths = (
            Path("artifacts/phase-9/pareto-analysis.json"),
            Path("artifacts/phase-10/tradeoff-explanations.json"),
        )

        for relative_path in report_paths:
            with self.subTest(report=str(relative_path)):
                self.assertEqual(
                    _sha256(PROJECT_ROOT / relative_path),
                    _documented_sha256(document, relative_path),
                )


def _documented_sha256(document: str, relative_path: Path) -> str:
    portable_path = relative_path.as_posix()
    match = re.search(
        rf"{re.escape(portable_path)}\nSHA256 ([0-9a-f]{{64}})",
        document,
    )
    if match is None:
        raise AssertionError(f"missing documented SHA256 for {portable_path}")
    return match.group(1)


def _documented_integer(document: str, pattern: str) -> int:
    match = re.search(pattern, document)
    if match is None:
        raise AssertionError(f"missing documented value matching {pattern}")
    return int(match.group(1))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _is_unsafe_archive_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    has_windows_drive = len(normalized) >= 2 and normalized[1] == ":"
    return (
        not normalized
        or path.is_absolute()
        or has_windows_drive
        or ".." in path.parts
    )


if __name__ == "__main__":
    unittest.main()
