import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from signalbudget.coverage import detection_readiness, investigation_readiness, source_ids
from signalbudget.loaders import (
    load_catalog_bundle,
    load_restricted_yaml,
    package_data_root,
    project_root,
)

PACKAGED_DATA_FILES = (
    "catalog/log_sources.yaml",
    "catalog/detection_dependencies.yaml",
    "catalog/investigation_questions.yaml",
    "contracts/detfuzz_result_schema.json",
    "measurements/detfuzz_lab_measurements.yaml",
    "measurements/source_volumes_lab_sample.yaml",
    "pricing/microsoft_sentinel_eastus_2026-07-23.yaml",
)


class CatalogTests(unittest.TestCase):
    def test_loads_phase8_catalogs(self) -> None:
        bundle = load_catalog_bundle(project_root())

        self.assertEqual(bundle.detection_dependencies["schema_version"], "1.0")
        self.assertEqual(len(bundle.log_sources["sources"]), 3)
        self.assertEqual(len(bundle.detection_dependencies["detections"]), 3)
        self.assertEqual(len(bundle.investigation_questions["questions"]), 5)
        self.assertEqual(bundle.pricing["vendor"], "Microsoft")
        self.assertEqual(bundle.pricing["retrieved_at"], "2026-07-23T00:00:00Z")
        self.assertEqual(bundle.pricing["meters"][0]["retail_price"], 4.3)
        self.assertEqual(
            bundle.pricing["meters"][1]["meter_name"],
            "Basic Logs Data Ingestion",
        )
        self.assertEqual(bundle.pricing["meters"][1]["unit_price"], 0.5)
        self.assertEqual(
            bundle.pricing["meters"][2]["meter_name"],
            "Auxiliary Logs Data Ingestion",
        )
        self.assertTrue(
            all(
                meter["billing_basis"] == "ingested_gb"
                for meter in bundle.pricing["meters"]
            )
        )

    def test_default_loader_uses_packaged_data(self) -> None:
        bundle = load_catalog_bundle()

        self.assertEqual(len(bundle.log_sources["sources"]), 3)
        self.assertEqual(bundle.pricing["vendor"], "Microsoft")

    def test_packaged_data_matches_repository_sources(self) -> None:
        root = project_root()
        packaged = package_data_root()

        for relative_path in PACKAGED_DATA_FILES:
            self.assertEqual(
                (packaged / relative_path)
                .read_text(encoding="utf-8-sig")
                .splitlines(),
                (root / relative_path)
                .read_text(encoding="utf-8-sig")
                .splitlines(),
                relative_path,
            )

    def test_readiness_uses_source_dependencies(self) -> None:
        bundle = load_catalog_bundle(project_root())
        available = source_ids(bundle.log_sources)

        detections = detection_readiness(bundle.detection_dependencies, available)
        questions = investigation_readiness(bundle.investigation_questions, available)

        self.assertTrue(all(detections.values()))
        self.assertTrue(all(questions.values()))

    def test_inline_list_parser_preserves_quoted_commas(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "quoted-list.yaml"
            path.write_text(
                'schema_version: "1.0"\n'
                "values: ['a, b', \"c, d\", plain]\n",
                encoding="utf-8",
            )

            payload = load_restricted_yaml(path)

        self.assertEqual(payload["values"], ["a, b", "c, d", "plain"])

    def test_inline_list_parser_rejects_malformed_lists(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "bad-list.yaml"
            path.write_text("values: [alpha, , beta]\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "empty item in inline list"):
                load_restricted_yaml(path)


if __name__ == "__main__":
    unittest.main()
