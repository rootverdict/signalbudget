import unittest

from signalbudget.costing import (
    cost_boundary_text,
    estimate_monthly_source_costs,
    summarize_selected_source_costs,
)
from signalbudget.loaders import load_catalog_bundle, project_root


class CostingTests(unittest.TestCase):
    def test_estimates_sysmon_cost_from_24h_lab_measurement(self) -> None:
        bundle = load_catalog_bundle(project_root())

        costs = estimate_monthly_source_costs(bundle.source_volumes, bundle.pricing)

        sysmon = costs["sysmon_process_create"]
        self.assertEqual(
            sysmon["cost_status"],
            "ESTIMATED_FROM_24H_LAB_MEASUREMENT",
        )
        self.assertAlmostEqual(sysmon["estimated_monthly_gb"], 0.058122)
        self.assertAlmostEqual(sysmon["estimated_monthly_cost_usd"], 0.2499246)

    def test_estimates_all_sources_from_24h_lab_measurements(self) -> None:
        bundle = load_catalog_bundle(project_root())
        costs = estimate_monthly_source_costs(bundle.source_volumes, bundle.pricing)

        powershell = costs["powershell_script_block"]
        security = costs["windows_security_logon"]

        self.assertEqual(
            powershell["cost_status"],
            "ESTIMATED_FROM_24H_LAB_MEASUREMENT",
        )
        self.assertAlmostEqual(powershell["estimated_monthly_cost_usd"], 0.0031863)
        self.assertEqual(
            security["cost_status"],
            "ESTIMATED_FROM_24H_LAB_MEASUREMENT",
        )
        self.assertAlmostEqual(security["estimated_monthly_cost_usd"], 0.04908321)

    def test_basic_tier_uses_ingestion_meter(self) -> None:
        bundle = load_catalog_bundle(project_root())
        costs = estimate_monthly_source_costs(
            {
                "volume_profiles": [
                    {
                        "source_id": "basic",
                        "measurement_status": "lab_24h_measurement",
                        "estimated_gb_per_day": 1.0,
                        "pricing_log_tier": "Basic Logs",
                    }
                ]
            },
            bundle.pricing,
        )

        self.assertEqual(costs["basic"]["unit_price_per_gb_usd"], 0.5)
        self.assertEqual(costs["basic"]["estimated_monthly_cost_usd"], 15.0)

    def test_mixed_configuration_reports_complete_cost(self) -> None:
        bundle = load_catalog_bundle(project_root())
        costs = estimate_monthly_source_costs(bundle.source_volumes, bundle.pricing)

        summary = summarize_selected_source_costs(
            ["sysmon_process_create", "powershell_script_block"],
            costs,
        )

        self.assertEqual(summary["cost_status"], "ESTIMATED_FROM_24H_LAB_MEASUREMENT")
        self.assertEqual(summary["missing_volume_sources"], [])
        self.assertAlmostEqual(summary["estimated_monthly_cost_usd"], 0.2531109)

    def test_cost_boundary_text_is_generated_from_source_costs(self) -> None:
        bundle = load_catalog_bundle(project_root())
        costs = estimate_monthly_source_costs(bundle.source_volumes, bundle.pricing)

        text = cost_boundary_text(costs)

        self.assertIn("sysmon_process_create: lab_24h_measurement", text)
        self.assertIn("ESTIMATED_FROM_24H_LAB_MEASUREMENT", text)
        self.assertIn("powershell_script_block: lab_24h_measurement", text)
        self.assertIn("windows_security_logon: lab_24h_measurement", text)

    def test_mixed_configuration_preserves_mixed_estimate_provenance(self) -> None:
        summary = summarize_selected_source_costs(
            ["measured", "generic"],
            {
                "measured": {
                    "estimated_monthly_cost_usd": 1.0,
                    "cost_status": "ESTIMATED_FROM_24H_LAB_MEASUREMENT",
                },
                "generic": {
                    "estimated_monthly_cost_usd": 2.0,
                    "cost_status": "ESTIMATED",
                },
            },
        )

        self.assertEqual(summary["cost_status"], "MIXED_ESTIMATE_PROVENANCE")

    def test_zero_cost_measurement_is_preserved_in_partial_summary(self) -> None:
        summary = summarize_selected_source_costs(
            ["free", "missing"],
            {
                "free": {
                    "estimated_monthly_cost_usd": 0.0,
                    "cost_status": "ESTIMATED",
                },
                "missing": {
                    "estimated_monthly_cost_usd": None,
                },
            },
        )

        self.assertEqual(summary["known_monthly_cost_usd"], 0.0)
        self.assertIsNone(summary["estimated_monthly_cost_usd"])
        self.assertEqual(summary["cost_status"], "PARTIAL_VOLUME_MEASUREMENT")
        self.assertEqual(summary["missing_volume_sources"], ["missing"])


if __name__ == "__main__":
    unittest.main()
