import argparse
import copy
import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from signalbudget.cli import configurations, main
from signalbudget.loaders import CatalogBundle, load_catalog_bundle, project_root


class CliTests(unittest.TestCase):
    def test_no_subcommand_defaults_to_summary(self) -> None:
        output = io.StringIO()

        with patch("sys.argv", ["signalbudget"]):
            with redirect_stdout(output):
                main()

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["log_sources"], 3)

    def test_configuration_count_is_derived_from_catalog(self) -> None:
        bundle = load_catalog_bundle(project_root())
        log_sources = copy.deepcopy(bundle.log_sources)
        log_sources["sources"].append(
            {
                "id": "fourth_source",
                "required_fields": [],
            }
        )
        source_volumes = copy.deepcopy(bundle.source_volumes)
        source_volumes["volume_profiles"].append(
            {
                "source_id": "fourth_source",
                "measurement_status": "pending",
                "estimated_gb_per_day": None,
                "pricing_log_tier": "Analytics Logs",
            }
        )
        expanded = CatalogBundle(
            log_sources=log_sources,
            detection_dependencies=bundle.detection_dependencies,
            investigation_questions=bundle.investigation_questions,
            measurements=bundle.measurements,
            source_volumes=source_volumes,
            pricing=bundle.pricing,
        )
        output = io.StringIO()

        with patch("signalbudget.cli.load_catalog_bundle", return_value=expanded):
            with redirect_stdout(output):
                configurations(argparse.Namespace(root=None))

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["configuration_count"], 16)
        self.assertEqual(payload["configuration_count"], len(payload["configurations"]))


if __name__ == "__main__":
    unittest.main()
