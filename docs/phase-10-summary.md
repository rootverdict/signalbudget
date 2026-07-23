# Phase 10 Summary

Phase 10 adds pricing freshness and generated tradeoff explanations.

## Implemented

- Pricing freshness status was renamed consistently:
  - `PRICING_FRESH`
  - `PRICING_STALE`
- `pareto-analysis` now exposes `pricing_status` at the top level.
- `explain-tradeoffs` CLI command generates JSON and Markdown reports.
- Source-removal losses are generated from catalog diffs, not hand-written text.
- Frontier narratives use only non-dominated configurations.
- The first frontier narrative is an explicit baseline entry.
- A single lab evidence caveat is reused in generated output.

## Command

```powershell
$env:PYTHONPATH='src'
Expand-Archive evidence\detfuzz-signalbudget-results-20260723-212216-posix.zip -DestinationPath build\v1-evidence
$run = 'build\v1-evidence\4ddc2989-4c84-49fe-801e-996c67a5702f'
python -m signalbudget.cli explain-tradeoffs --output-dir artifacts\phase-10 --detfuzz-result "$run\reports\suite-report.json" --detfuzz-evidence-root "$run\evidence"
```

## Current Result

Pricing is fresh:

```text
PRICING_FRESH
```

Removing `sysmon_process_create` loses the DetFuzz-validated encoded
PowerShell detection plus process command-line and parent-child investigation
questions.

The generated frontier narrative starts at:

```text
Baseline: none
```

Then it walks adjacent non-dominated configurations in non-decreasing cost
order.

## Evidence Boundary

Cost estimates are lab-derived from 24-hour VM measurements and are not
production forecasts.

## Status

```text
Phase 10 code complete
Phase 10 freshness rename complete
Phase 10 loss explanations complete
Phase 10 frontier narratives complete
Phase 10 unit tests complete
```
