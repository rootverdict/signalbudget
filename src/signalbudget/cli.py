from __future__ import annotations

import argparse
import json
from pathlib import Path

from signalbudget.configurations import enumerate_source_configurations
from signalbudget.contracts import validate_detfuzz_result_file
from signalbudget.costing import cost_boundary_text, estimate_monthly_source_costs
from signalbudget.coverage import detection_readiness, investigation_readiness, source_ids
from signalbudget.freshness import pricing_freshness
from signalbudget.loaders import load_catalog_bundle
from signalbudget.pareto import analyze_pareto, render_pareto_markdown
from signalbudget.tradeoffs import build_tradeoff_report, render_tradeoff_markdown


def summarize(args: argparse.Namespace) -> None:
    bundle = load_catalog_bundle(args.root)
    sources = source_ids(bundle.log_sources)
    payload = {
        "schema_version": "1.0",
        "log_sources": len(bundle.log_sources.get("sources", [])),
        "detections": len(bundle.detection_dependencies.get("detections", [])),
        "investigation_questions": len(
            bundle.investigation_questions.get("questions", [])
        ),
        "measurements": len(bundle.measurements.get("measurements", [])),
        "source_volume_profiles": len(
            bundle.source_volumes.get("volume_profiles", [])
        ),
        "pricing_vendor": bundle.pricing.get("vendor"),
        "pricing_product": bundle.pricing.get("product"),
        "pricing_region": bundle.pricing.get("region"),
        "pricing_meters": len(bundle.pricing.get("meters", [])),
        "pricing_freshness": pricing_freshness(bundle.pricing),
        "detection_readiness": detection_readiness(
            bundle.detection_dependencies, sources, bundle.log_sources
        ),
        "investigation_readiness": investigation_readiness(
            bundle.investigation_questions, sources, bundle.log_sources
        ),
        "boundary": (
            "SignalBudget consumes exported DetFuzz JSON; "
            "it must not import detfuzz.* code."
        ),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def validate_detfuzz(args: argparse.Namespace) -> None:
    result = validate_detfuzz_result_file(
        args.path,
        evidence_root=args.evidence_root,
        require_suite_contract=args.require_suite_contract,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def configurations(args: argparse.Namespace) -> None:
    bundle = load_catalog_bundle(args.root)
    source_costs = estimate_monthly_source_costs(
        bundle.source_volumes,
        bundle.pricing,
    )
    configuration_payload = enumerate_source_configurations(
        bundle.log_sources,
        bundle.detection_dependencies,
        bundle.investigation_questions,
        source_costs,
    )
    payload = {
        "schema_version": "1.0",
        "configuration_count": len(configuration_payload),
        "cost_boundary": cost_boundary_text(source_costs),
        "source_costs": source_costs,
        "configurations": configuration_payload,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def pareto(args: argparse.Namespace) -> None:
    bundle = load_catalog_bundle(args.root)
    detfuzz_summary = validate_detfuzz_result_file(
        args.detfuzz_result,
        evidence_root=args.detfuzz_evidence_root,
        require_suite_contract=True,
    )
    source_costs = estimate_monthly_source_costs(
        bundle.source_volumes,
        bundle.pricing,
    )
    configurations_payload = enumerate_source_configurations(
        bundle.log_sources,
        bundle.detection_dependencies,
        bundle.investigation_questions,
        source_costs,
        set(detfuzz_summary["validated_rule_ids"]),
    )
    analysis = analyze_pareto(configurations_payload)
    freshness = pricing_freshness(bundle.pricing)
    if args.fail_on_stale_pricing and not freshness["fresh"]:
        raise SystemExit(f"pricing is not fresh: {freshness['status']}")
    analysis["pricing_status"] = freshness["status"]
    analysis["pricing"] = freshness
    analysis["detfuzz_contract"] = detfuzz_summary
    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = args.output_dir / "pareto-analysis.json"
        markdown_path = args.output_dir / "pareto-analysis.md"
        json_path.write_text(
            json.dumps(analysis, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        markdown_path.write_text(render_pareto_markdown(analysis), encoding="utf-8")
        analysis["outputs"] = {
            "json_report": str(json_path),
            "markdown_report": str(markdown_path),
        }
    print(json.dumps(analysis, indent=2, sort_keys=True))


def explain_tradeoffs(args: argparse.Namespace) -> None:
    bundle = load_catalog_bundle(args.root)
    detfuzz_summary = validate_detfuzz_result_file(
        args.detfuzz_result,
        evidence_root=args.detfuzz_evidence_root,
        require_suite_contract=True,
    )
    report = build_tradeoff_report(bundle, set(detfuzz_summary["validated_rule_ids"]))
    report["detfuzz_contract"] = detfuzz_summary
    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = args.output_dir / "tradeoff-explanations.json"
        markdown_path = args.output_dir / "tradeoff-explanations.md"
        json_path.write_text(
            json.dumps(report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        markdown_path.write_text(render_tradeoff_markdown(report), encoding="utf-8")
        report["outputs"] = {
            "json_report": str(json_path),
            "markdown_report": str(markdown_path),
        }
    print(json.dumps(report, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="signalbudget")
    parser.set_defaults(root=None)
    subcommands = parser.add_subparsers(dest="command")

    summary = subcommands.add_parser(
        "summarize",
        help="Load Phase 8 catalogs and print a machine-readable summary.",
    )
    summary.add_argument(
        "--root",
        type=Path,
        default=None,
        help="SignalBudget project root. Defaults to the installed source tree.",
    )

    validate = subcommands.add_parser(
        "validate-detfuzz",
        help="Validate a DetFuzz JSON artifact against the Phase 8 import contract.",
    )
    validate.add_argument("--path", type=Path, required=True)
    validate.add_argument("--evidence-root", type=Path, default=None)
    validate.add_argument(
        "--require-suite-contract",
        action="store_true",
        help="Require full B0-M5-NC1-B1 suite health and verified evidence hashes.",
    )

    configs = subcommands.add_parser(
        "enumerate-configurations",
        help="Enumerate the eight Phase 8 source combinations without Pareto ranking.",
    )
    configs.add_argument(
        "--root",
        type=Path,
        default=None,
        help="SignalBudget project root. Defaults to the installed source tree.",
    )

    pareto_parser = subcommands.add_parser(
        "pareto-analysis",
        help="Run Pareto analysis over the eight Phase 9 telemetry configurations.",
    )
    pareto_parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="SignalBudget project root. Defaults to the installed source tree.",
    )
    pareto_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for JSON and Markdown Pareto reports.",
    )
    pareto_parser.add_argument(
        "--detfuzz-result",
        type=Path,
        required=True,
        help="Verified DetFuzz suite report JSON used for validated coverage.",
    )
    pareto_parser.add_argument("--detfuzz-evidence-root", type=Path, default=None)
    pareto_parser.add_argument("--fail-on-stale-pricing", action="store_true")

    tradeoffs = subcommands.add_parser(
        "explain-tradeoffs",
        help="Explain pricing freshness, source removal losses, and frontier tradeoffs.",
    )
    tradeoffs.add_argument(
        "--root",
        type=Path,
        default=None,
        help="SignalBudget project root. Defaults to the installed source tree.",
    )
    tradeoffs.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for JSON and Markdown tradeoff reports.",
    )
    tradeoffs.add_argument(
        "--detfuzz-result",
        type=Path,
        required=True,
        help="Verified DetFuzz suite report JSON used for validated coverage.",
    )
    tradeoffs.add_argument("--detfuzz-evidence-root", type=Path, default=None)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command in {None, "summarize"}:
        summarize(args)
        return

    if args.command == "validate-detfuzz":
        validate_detfuzz(args)
        return

    if args.command == "enumerate-configurations":
        configurations(args)
        return

    if args.command == "pareto-analysis":
        pareto(args)
        return

    if args.command == "explain-tradeoffs":
        explain_tradeoffs(args)
        return

    parser.error(f"unsupported command: {args.command}")


if __name__ == "__main__":
    main()
