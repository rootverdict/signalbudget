# Evidence Index

This file lists the main evidence artifacts and what each one proves.

## DetFuzz Import Boundary

`contracts/detfuzz_result_schema.json`

Defines the versioned DetFuzz JSON contract SignalBudget accepts.

`tests/fixtures/benign-results.json`

Fixture derived from DetFuzz Phase 7 benign evidence. Used to validate the data
contract and false-positive findings.

`tests/fixtures/phase6-b0-suite-report.json`

Fixture representing the DetFuzz Phase 6 B0 encoded PowerShell result.

`tests/test_no_detfuzz_imports.py`

Proves `src/signalbudget/` does not import `detfuzz.*` code. The repository
`integration_tests/` directory is an explicit exception for cross-package
compatibility checks and is not part of the installed SignalBudget package.

## Pricing Evidence

`pricing/microsoft_sentinel_eastus_2026-07-23.yaml`

Versioned Microsoft Sentinel pricing data with:

```text
retrieved_at
effective_date
max_age_days
source_url
```

`src/signalbudget/freshness.py`

Computes `PRICING_FRESH` or `PRICING_STALE`.

## Volume Evidence

`measurements/source_volumes_lab_sample.yaml`

Stores the 24-hour lab VM event counts and XML byte-size samples:

```text
sysmon_process_create: 898 events
powershell_script_block: 9 events
windows_security_logon: 208 events
```

These measurements are lab-scoped and not production forecasts.

## Pareto Evidence

`artifacts/phase-9/pareto-analysis.json`

Machine-readable Pareto result regenerated from the real DetFuzz VM suite
`dc017824-0d4e-41d0-9d32-610b410accb0`.

`artifacts/phase-9/pareto-analysis.md`

Human-readable Pareto report.

Current key claims:

```text
configuration_count: 8
complete_cost_configuration_count: 8
partial_cost_configuration_count: 0
pricing_status: PRICING_FRESH
dominated: windows_security_logon
```

## Tradeoff Evidence

`artifacts/phase-10/tradeoff-explanations.json`

Machine-readable pricing freshness, source-removal losses, and frontier
tradeoffs regenerated from the real DetFuzz VM suite
`dc017824-0d4e-41d0-9d32-610b410accb0`.

`artifacts/phase-10/tradeoff-explanations.md`

Human-readable tradeoff report.

Current key claim:

```text
Removing sysmon_process_create loses rule
`d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62`
(`detfuzz-v0-powershell-encoded-command`).
```

## Test Evidence

`tests/`

The final expected test result is:

```text
OK
```

## VM Evidence Status

Final Phase 9 and Phase 10 reports are backed by the real DetFuzz Windows VM
suite `dc017824-0d4e-41d0-9d32-610b410accb0`, not by the strict test fixture.
See `docs/phase-11-vm-validation.md` for the final evidence package details.

The historical archive is not committed to or currently published by this
source repository. Its recorded name and checksum are:

```text
portfolio-v0-evidence.zip
SHA256 7c58fd3ee092abf19841f6ea738f4674d6f138e81e779731283077b3d577dd85
```

This checksum preserves provenance but does not make the archive independently
retrievable. A fresh clone can verify the checked-in Phase 9/10 report hashes
and run the synthetic strict-contract fixture; revalidating the historical raw
VM suite requires a separately supplied copy of the archive.

The archive contains clock preflight, the failed first calibration, the passing
calibration retry, eight matched Sysmon XML events, the canonical DetFuzz suite
report, a 63-file evidence manifest, and the SignalBudget Phase 9/10 reports
generated from that same suite report.

Final validation:

```text
SignalBudget unit tests: pass
Cross-project integration: 1 passed
Strict DetFuzz contract: 63/63 evidence hashes verified
```
