import unittest

from signalbudget.configurations import enumerate_source_configurations
from signalbudget.costing import estimate_monthly_source_costs
from signalbudget.loaders import load_catalog_bundle, project_root
from signalbudget.pareto import analyze_pareto, dominates, render_pareto_markdown


class ParetoTests(unittest.TestCase):
    def test_dominance_requires_complete_cost_and_strict_improvement(self) -> None:
        cheap_low_value = {
            "estimated_monthly_cost_usd": 0.0,
            "validated_detection_count": 0,
            "investigation_question_ready_count": 0,
        }
        costly_high_value = {
            "estimated_monthly_cost_usd": 0.25,
            "validated_detection_count": 1,
            "investigation_question_ready_count": 2,
        }
        unknown_cost = {
            "estimated_monthly_cost_usd": None,
            "validated_detection_count": 3,
            "investigation_question_ready_count": 5,
        }

        self.assertFalse(dominates(cheap_low_value, costly_high_value))
        self.assertFalse(dominates(costly_high_value, cheap_low_value))
        self.assertFalse(dominates(unknown_cost, cheap_low_value))

    def test_analyzes_current_phase9_frontier(self) -> None:
        bundle = load_catalog_bundle(project_root())
        source_costs = estimate_monthly_source_costs(
            bundle.source_volumes,
            bundle.pricing,
        )
        configurations = enumerate_source_configurations(
            bundle.log_sources,
            bundle.detection_dependencies,
            bundle.investigation_questions,
            source_costs,
            {"d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62"},
        )

        analysis = analyze_pareto(configurations)
        non_dominated = {
            config["configuration_id"] for config in analysis["non_dominated"]
        }
        dominated = {config["configuration_id"] for config in analysis["dominated"]}
        security_only = next(
            config
            for config in analysis["dominated"]
            if config["configuration_id"] == "windows_security_logon"
        )

        self.assertEqual(analysis["configuration_count"], 8)
        self.assertEqual(analysis["complete_cost_configuration_count"], 8)
        self.assertEqual(analysis["partial_cost_configuration_count"], 0)
        self.assertEqual(
            non_dominated,
            {
                "none",
                "powershell_script_block",
                "powershell_script_block+windows_security_logon",
                "sysmon_process_create",
                "sysmon_process_create+powershell_script_block",
                "sysmon_process_create+windows_security_logon",
                "sysmon_process_create+powershell_script_block+windows_security_logon",
            },
        )
        self.assertEqual(dominated, {"windows_security_logon"})
        self.assertEqual(security_only["dominated_by"], ["powershell_script_block"])
        self.assertFalse(analysis["pending_cost"])
        self.assertIn("All configurations have complete", analysis["cost_boundary"])
        self.assertIn(
            "sysmon_process_create+powershell_script_block+windows_security_logon",
            non_dominated,
        )

    def test_renders_markdown_report(self) -> None:
        analysis = {
            "configuration_count": 1,
            "complete_cost_configuration_count": 1,
            "partial_cost_configuration_count": 0,
            "non_dominated": [
                {
                    "configuration_id": "none",
                    "pareto_status": "NON_DOMINATED",
                    "estimated_monthly_cost_usd": 0.0,
                    "validated_detection_count": 0,
                    "investigation_question_ready_count": 0,
                }
            ],
            "pending_cost": [],
            "dominated": [],
            "cost_boundary": "boundary",
        }

        markdown = render_pareto_markdown(analysis)

        self.assertIn("# SignalBudget Pareto Analysis", markdown)
        self.assertIn("`none`", markdown)
        self.assertNotIn("Pending Cost Configurations", markdown)


if __name__ == "__main__":
    unittest.main()
