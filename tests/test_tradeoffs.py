import unittest

from signalbudget.loaders import load_catalog_bundle, project_root
from signalbudget.tradeoffs import (
    LAB_ESTIMATE_CAVEAT,
    build_tradeoff_report,
    render_tradeoff_markdown,
)


class TradeoffTests(unittest.TestCase):
    def test_report_surfaces_pricing_status_at_top_level(self) -> None:
        report = build_tradeoff_report(load_catalog_bundle(project_root()))

        self.assertEqual(report["pricing_status"], "PRICING_FRESH")
        self.assertEqual(report["pricing"]["status"], "PRICING_FRESH")

    def test_removing_sysmon_loses_validated_detfuzz_detection(self) -> None:
        report = build_tradeoff_report(load_catalog_bundle(project_root()))
        sysmon_loss = next(
            loss
            for loss in report["source_removal_losses"]
            if loss["removed_source"] == "sysmon_process_create"
        )
        lost_detection_ids = {
            detection["id"] for detection in sysmon_loss["lost_detections"]
        }
        lost_question_ids = {
            question["id"] for question in sysmon_loss["lost_investigation_questions"]
        }

        self.assertIn("d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62", lost_detection_ids)
        self.assertIn("process_command_line", lost_question_ids)
        self.assertIn("parent_child_process", lost_question_ids)

    def test_frontier_narrative_uses_only_non_dominated_configs(self) -> None:
        report = build_tradeoff_report(load_catalog_bundle(project_root()))
        frontier_ids = set(report["pareto_summary"]["non_dominated_configuration_ids"])
        narrated_ids = {report["frontier_tradeoffs"][0]["configuration_id"]}
        for tradeoff in report["frontier_tradeoffs"][1:]:
            narrated_ids.add(tradeoff["from_configuration_id"])
            narrated_ids.add(tradeoff["to_configuration_id"])

        self.assertEqual(narrated_ids, frontier_ids)
        self.assertNotIn("windows_security_logon", narrated_ids)

    def test_first_frontier_narrative_is_baseline(self) -> None:
        report = build_tradeoff_report(load_catalog_bundle(project_root()))
        first = report["frontier_tradeoffs"][0]

        self.assertEqual(first["type"], "baseline")
        self.assertEqual(first["configuration_id"], "none")
        self.assertIn("Baseline:", first["narrative"])

    def test_frontier_costs_are_non_decreasing(self) -> None:
        report = build_tradeoff_report(load_catalog_bundle(project_root()))
        previous_cost = float(
            report["frontier_tradeoffs"][0]["estimated_monthly_cost_usd"]
        )
        for tradeoff in report["frontier_tradeoffs"][1:]:
            current_cost = float(tradeoff["to_estimated_monthly_cost_usd"])
            self.assertGreaterEqual(current_cost, previous_cost)
            previous_cost = current_cost

    def test_caveat_appears_in_json_and_markdown(self) -> None:
        report = build_tradeoff_report(load_catalog_bundle(project_root()))
        markdown = render_tradeoff_markdown(report)

        self.assertEqual(report["evidence_caveat"], LAB_ESTIMATE_CAVEAT)
        self.assertIn(LAB_ESTIMATE_CAVEAT, markdown)


if __name__ == "__main__":
    unittest.main()
