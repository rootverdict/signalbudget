import unittest

from signalbudget.coverage import detection_readiness, investigation_readiness, source_ids
from signalbudget.loaders import load_catalog_bundle, project_root


class CatalogTests(unittest.TestCase):
    def test_loads_phase8_catalogs(self) -> None:
        bundle = load_catalog_bundle(project_root())

        self.assertEqual(len(bundle.log_sources["sources"]), 3)
        self.assertEqual(len(bundle.detection_dependencies["detections"]), 3)
        self.assertEqual(len(bundle.investigation_questions["questions"]), 5)
        self.assertEqual(bundle.pricing["vendor"], "Microsoft")
        self.assertEqual(bundle.pricing["meters"][0]["retail_price"], 4.3)

    def test_readiness_uses_source_dependencies(self) -> None:
        bundle = load_catalog_bundle(project_root())
        available = source_ids(bundle.log_sources)

        detections = detection_readiness(bundle.detection_dependencies, available)
        questions = investigation_readiness(bundle.investigation_questions, available)

        self.assertTrue(all(detections.values()))
        self.assertTrue(all(questions.values()))


if __name__ == "__main__":
    unittest.main()
