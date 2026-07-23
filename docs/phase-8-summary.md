# Phase 8 Summary

Phase 8 starts SignalBudget with a small, reproducible catalog and a strict
DetFuzz data-only import boundary.

## Implemented

- Separate `signalbudget/` project.
- Versioned DetFuzz result contract in `contracts/detfuzz_result_schema.json`.
- Three-source log catalog:
  - Sysmon Process Create, Event ID 1
  - PowerShell Script Block Logging, Event ID 4104
  - Windows Security logon events, Event IDs 4624 and 4625
- Detection dependency catalog.
- Investigation-question catalog.
- Lab measurement notes derived from DetFuzz evidence.
- Source volume profile with a real 24-hour Sysmon lab measurement.
- Real Microsoft Sentinel pricing profile for East US.
- Loader and validation CLI.
- Eight source combinations enumerated; Phase 9 later completed cost estimates
  for all combinations.
- Dynamic `cost_boundary` text generated from source cost status.
- Pricing freshness check using `retrieved_at` and `max_age_days`.
- Test that fails if `src/signalbudget/` imports `detfuzz.*` code.

The configuration output uses `telemetry_ready_detection_count`, not
`validated_detection_count`, because only the DetFuzz v0 rule is validated by
real evidence so far.

## Pricing Source

Pricing was retrieved from Microsoft's official Azure Retail Prices API on
2026-07-21 and the ingestion-meter classifications were reverified on
2026-07-23.

```text
Microsoft Sentinel East US Pay-as-you-go Analysis: 4.30 USD / GB
Azure Monitor East US Basic Logs Data Ingestion: 0.50 USD / GB
Azure Monitor East US Auxiliary Logs Data Ingestion: 0.05 USD / GB
```

Basic and Auxiliary query-analysis meters are separate usage dimensions and
are not used as ingestion prices.

Actual pricing may vary by agreement, currency, taxes, and purchase date.

## Evidence Boundary

SignalBudget consumes DetFuzz exported JSON only. It must not import
`detfuzz.*` code from `src/signalbudget/`. This boundary is enforced by
`tests/test_no_detfuzz_imports.py`. The repository-level `integration_tests/`
directory is an intentional exception for cross-package compatibility checks
and is not part of the deployable SignalBudget package.

## Measurement Boundary

Phase 8 now computes a Sysmon cost using a real 24-hour VM measurement:

```text
source: sysmon_process_create
events_observed: 898
sample_events_exported: 100
sample_xml_bytes_observed: 215745
bytes_per_event_observed: 2157.45
estimated_events_per_day: 898
estimated_gb_per_day: 0.0019374
pricing: Microsoft Sentinel Analytics Logs, 4.30 USD / GB
estimated_monthly_proxy_cost_usd: 0.2499246
cost_estimate_kind: XML_EXPORT_SIZE_PROXY
```

This is labeled `ESTIMATED_FROM_24H_LAB_MEASUREMENT`. It is still a lab estimate,
not a production bill forecast, but it is no longer based on a single saved XML
event.

PowerShell Script Block and Windows Security initially had 24-hour event counts
without byte-size samples. Phase 9 completed those measurements and computed
cost for all eight source configurations. The measurement windows include
DetFuzz test execution activity, so they are not pure idle-baseline
measurements.

## Status

```text
Phase 8 code complete
Phase 8 catalog complete
Phase 8 pricing profile complete
Phase 8 source combinations enumerated
Sysmon 24-hour cost estimate complete
Phase 8 unit tests complete
```

Next phase status is tracked in `docs/phase-9-summary.md`.
