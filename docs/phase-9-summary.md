# Phase 9 Summary

Phase 9 adds Pareto analysis for the eight telemetry source configurations.

## Implemented

- Pareto engine over:
  - lower monthly cost,
  - higher validated detection coverage,
  - higher investigation utility.
- `pareto-analysis` CLI command.
- Optional JSON and Markdown report output.
- Complete-cost and partial-cost configurations are separated.
- Partial-cost configurations are not falsely ranked as final Pareto choices.
- All three source volume profiles now have lab-derived byte-size estimates.
- Tests for dominance logic, current frontier, and Markdown rendering.

## Current Result

All eight configurations now have complete lab-derived cost estimates from
24-hour VM event counts and XML byte-size samples.

Seven configurations are currently non-dominated:

```text
none
powershell_script_block
powershell_script_block+windows_security_logon
sysmon_process_create
sysmon_process_create+powershell_script_block
sysmon_process_create+windows_security_logon
sysmon_process_create+powershell_script_block+windows_security_logon
```

One configuration is dominated:

```text
windows_security_logon
```

`windows_security_logon` is dominated by `powershell_script_block` in this lab
measurement because both provide one investigation question and zero validated
DetFuzz detections, while PowerShell Script Block is cheaper.

This is a narrow lab finding, not a general claim that Windows Security logging
is always more expensive. The cost difference is driven by the observed event
volume in one lightly used 24-hour VM window; production logon volume can change
that tradeoff.

Key monthly lab estimates:

```text
powershell_script_block: $0.00318630
windows_security_logon: $0.04908321
sysmon_process_create: $0.24992460
all three sources: $0.30219411
```

## Command

```powershell
$env:PYTHONPATH='src'
Expand-Archive evidence\detfuzz-signalbudget-results-20260723-212216-posix.zip -DestinationPath build\v1-evidence
$run = 'build\v1-evidence\4ddc2989-4c84-49fe-801e-996c67a5702f'
python -m signalbudget.cli pareto-analysis --output-dir artifacts\phase-9 --detfuzz-result "$run\reports\suite-report.json" --detfuzz-evidence-root "$run\evidence"
```

## Evidence Boundary

Phase 9 does not use arbitrary weights. It also does not pretend partial-cost
configurations are fully comparable. In the current evidence set there are no
partial-cost configurations left; all eight are ranked using lab-derived cost
estimates. The lab estimates are useful for demonstrating the method, but they
should not be treated as production volume forecasts.

## Status

```text
Phase 9 code complete
Phase 9 Pareto engine complete
Phase 9 unit tests complete
Current Pareto result covers all eight source configurations
```
