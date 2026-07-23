# Phase 11 VM Validation

This document records the final portfolio evidence package for SignalBudget and
its DetFuzz input.

## Evidence Package

```text
portfolio-v0-evidence.zip
SHA256 7c58fd3ee092abf19841f6ea738f4674d6f138e81e779731283077b3d577dd85
```

The archive was produced as a historical portfolio release artifact. It is not
committed to this source repository; the paths used in the original packaged
release were:

```text
evidence/portfolio-v0-evidence.zip
evidence/portfolio-v0-evidence.sha256.txt
```

## DetFuzz VM Run

The real Windows VM suite is:

```text
suite_id: dc017824-0d4e-41d0-9d32-610b410accb0
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

The archive contains one matched Sysmon Event ID 1 XML file for each of the
eight cases.

## Preflight And Calibration

Clock preflight passed:

```text
status: PASS
reason: CLOCK_SYNC_OK
offset_ms: 313
time_sync_source: time.windows.com,0x9
```

The first calibration is retained as evidence because it failed honestly: three
of twenty baseline runs timed out during telemetry correlation under the initial
polling window.

The retry calibration passed:

```text
status: PASS
reason: CALIBRATION_HEALTHY
runs_completed: 20
selected telemetry_query timeout: 74 seconds
```

The final DetFuzz suite used the Python-written passing calibration file:

```text
C:\DetFuzz\portfolio-v0\calibration-pass\4fd3d9d8-a9f7-4d5f-91bc-40a6232f2e8e\timeout-calibration.json
```

## SignalBudget Validation

SignalBudget consumed the real DetFuzz suite report:

```powershell
python -m signalbudget.cli validate-detfuzz `
  --path C:\DetFuzz\portfolio-v0\runs\dc017824-0d4e-41d0-9d32-610b410accb0\reports\suite-report.json `
  --evidence-root C:\DetFuzz\portfolio-v0\runs\dc017824-0d4e-41d0-9d32-610b410accb0\evidence `
  --require-suite-contract
```

Validation result:

```text
suite_status: COMPLETED
evidence_files_checked: 63
evidence_hashes_verified: true
validated_rule_ids: d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62
```

## Generated Reports

The checked-in reports under `artifacts/phase-9` and `artifacts/phase-10` were
regenerated from the real DetFuzz suite above.

The JSON reports are byte-for-byte identical to the copies inside the evidence
archive:

```text
artifacts/phase-9/pareto-analysis.json
SHA256 5acb16cf4a8019cb6ff4bfa5ff2f3768f8bc687ae7824e236711781d44161703

artifacts/phase-10/tradeoff-explanations.json
SHA256 a2d1d19be6b3a49d6b48fd37ae0d3bd9f3cdbd254bb335c08c98732c100e22d6
```

## Boundary

This validates the final lab evidence and the DetFuzz-to-SignalBudget handoff.
The cost estimates remain lab-derived 24-hour VM estimates, not production
billing forecasts.
