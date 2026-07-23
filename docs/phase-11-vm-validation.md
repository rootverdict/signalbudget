# Phase 11 VM Validation

This document records the final local evidence package for SignalBudget v1 and
its DetFuzz input.

## Evidence Package

```text
evidence/detfuzz-signalbudget-results-20260723-212216-posix.zip
SHA256 2570ce74dd2d49d4af708b7a1153278c2aa01622e0b6fd1896c0787a3ceb4d4d
entries: 121
uncompressed bytes: 265658
unsafe archive paths: 0
```

The archive is included locally, so a fresh checkout containing the file can
independently verify the raw evidence and regenerate the reports.

## DetFuzz VM Run

```text
suite_id: 4ddc2989-4c84-49fe-801e-996c67a5702f
suite_status: COMPLETED
abort_reason: null
host: DetFuzz-Win11-Lab
telemetry: Microsoft-Windows-Sysmon/Operational
```

Case result summary:

```text
B0  DETECTED
M1  VALID_BYPASS
M2  DETECTED
M3  DETECTED
M4  DETECTED
M5  DETECTED
NC1 INVALID_MUTANT
B1  DETECTED
```

## Preflight And Calibration

Clock preflight passed:

```text
status: PASS
reason: CLOCK_SYNC_OK
offset_ms: 249
time_sync_source: time.windows.com,0x9
```

Calibration passed:

```text
status: PASS
reason: CALIBRATION_HEALTHY
runs_completed: 20
maximum_stable_timeout_seconds: 120
```

## Classification Compatibility

This DetFuzz producer finalized M1 as `VALID_BYPASS` in `suite-results.json`
and `suite-report.json`, while the hashed M1 `case-record.json` retained the
preliminary value `CANDIDATE_VALID_BYPASS`.

SignalBudget accepts only this exact mutation-case transition when
`preliminary_classification` also equals `CANDIDATE_VALID_BYPASS` and the
closing B1 baseline is healthy. The archive itself is not modified. The strict
validation result exposes the compatibility decision rather than hiding it.

## SignalBudget Validation

```powershell
Expand-Archive evidence\detfuzz-signalbudget-results-20260723-212216-posix.zip -DestinationPath build\v1-evidence
$run = 'build\v1-evidence\4ddc2989-4c84-49fe-801e-996c67a5702f'
python -m signalbudget.cli validate-detfuzz `
  --path "$run\reports\suite-report.json" `
  --evidence-root "$run\evidence" `
  --require-suite-contract
```

Validation result:

```text
suite_status: COMPLETED
evidence_files_checked: 63
evidence_hashes_verified: true
validated_rule_ids: d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62
legacy_preliminary_classifications_accepted: M1
```

## Generated Reports

The checked-in reports under `artifacts/phase-9` and `artifacts/phase-10` were
regenerated from this VM suite:

```text
artifacts/phase-9/pareto-analysis.json
SHA256 b47d5bab826c218802b02c9e18c5654af2f17bf441c1c49ea1e02c2dfb017daf

artifacts/phase-10/tradeoff-explanations.json
SHA256 1ace22d2886ec5fc885c866402f5f7f2ee9dac5920d8c618596b948a6c3463d3
```

## Boundary

This validates the final lab evidence and the DetFuzz-to-SignalBudget handoff.
The cost estimates remain lab-derived 24-hour VM estimates, not production
billing forecasts.
