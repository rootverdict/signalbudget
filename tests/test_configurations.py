import unittest

from signalbudget.configurations import enumerate_source_configurations
from signalbudget.costing import estimate_monthly_source_costs
from signalbudget.loaders import load_catalog_bundle, project_root


class ConfigurationTests(unittest.TestCase):
    def test_enumerates_all_eight_source_combinations(self) -> None:
        bundle = load_catalog_bundle(project_root())
        source_costs = estimate_monthly_source_costs(
            bundle.source_volumes,
            bundle.pricing,
        )

        configs = enumerate_source_configurations(
            bundle.log_sources,
            bundle.detection_dependencies,
            bundle.investigation_questions,
            source_costs,
        )

        self.assertEqual(len(configs), 8)
        self.assertEqual(configs[0]["configuration_id"], "none")
        self.assertTrue(
            any(
                config["configuration_id"]
                == "sysmon_process_create+powershell_script_block+windows_security_logon"
                for config in configs
            )
        )
        by_id = {config["configuration_id"]: config for config in configs}
        self.assertEqual(by_id["none"]["cost_status"], "NO_SOURCES_SELECTED")
        self.assertEqual(
            by_id["sysmon_process_create"]["cost_status"],
            "ESTIMATED_FROM_24H_LAB_MEASUREMENT",
        )
        self.assertGreater(
            by_id["sysmon_process_create"]["estimated_monthly_cost_usd"],
            0,
        )
        self.assertEqual(
            by_id["sysmon_process_create+powershell_script_block"]["cost_status"],
            "ESTIMATED_FROM_24H_LAB_MEASUREMENT",
        )
        self.assertEqual(
            by_id[
                "sysmon_process_create+powershell_script_block"
            ]["missing_volume_sources"],
            [],
        )

    def test_validated_detection_count_requires_detfuzz_artifact(self) -> None:
        bundle = load_catalog_bundle(project_root())
        source_costs = estimate_monthly_source_costs(
            bundle.source_volumes,
            bundle.pricing,
        )
        without_artifact = enumerate_source_configurations(
            bundle.log_sources,
            bundle.detection_dependencies,
            bundle.investigation_questions,
            source_costs,
        )
        with_artifact = enumerate_source_configurations(
            bundle.log_sources,
            bundle.detection_dependencies,
            bundle.investigation_questions,
            source_costs,
            {"d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62"},
        )

        self.assertEqual(
            {config["configuration_id"]: config for config in without_artifact}[
                "sysmon_process_create"
            ]["validated_detection_count"],
            0,
        )
        self.assertEqual(
            {config["configuration_id"]: config for config in with_artifact}[
                "sysmon_process_create"
            ]["validated_detection_count"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
