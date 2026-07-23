# SignalBudget v0 Evidence Index

This source repository contains the generated human-readable evidence reports:

```text
evidence/pareto-analysis.md
evidence/tradeoff-explanations.md
```

The historical raw VM archive is an external release artifact, not a file in
this repository. Its recorded name and checksum are:

```text
portfolio-v0-evidence.zip
SHA256 7c58fd3ee092abf19841f6ea738f4674d6f138e81e779731283077b3d577dd85
```

SignalBudget's checked-in Phase 9 and Phase 10 artifacts were regenerated from
the real DetFuzz VM suite:

```text
dc017824-0d4e-41d0-9d32-610b410accb0
```

The external evidence archive contains:

```text
runs/dc017824-0d4e-41d0-9d32-610b410accb0/reports/suite-report.json
runs/dc017824-0d4e-41d0-9d32-610b410accb0/reports/evidence-manifest.json
runs/dc017824-0d4e-41d0-9d32-610b410accb0/evidence/*/matched-sysmon-event.xml
signalbudget/phase-9/pareto-analysis.json
signalbudget/phase-10/tradeoff-explanations.json
```

Validation highlights:

```text
suite_status: COMPLETED
evidence_files_checked: 63
evidence_hashes_verified: true
pricing_status: PRICING_FRESH
configuration_count: 8
complete_cost_configuration_count: 8
partial_cost_configuration_count: 0
```

The cost estimates are lab-derived from a 24-hour Windows VM measurement and are
not production forecasts.
