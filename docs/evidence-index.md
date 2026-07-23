# Evidence Index

This file maps SignalBudget v1 claims to locally verifiable evidence.

## V1 Boundary

`docs/v1-scope.md`

Defines the required v1 capabilities, definition of done, exclusions, and v2
backlog.

## DetFuzz Import Boundary

`contracts/detfuzz_result_schema.json`

Defines the versioned DetFuzz JSON contract SignalBudget accepts.

`tests/fixtures/benign-results.json`

Exercises the base contract and benign classifications.

`tests/fixtures/full-suite-report.json` and `tests/fixtures/evidence/`

Provide a portable strict-contract fixture.

`tests/test_no_detfuzz_imports.py`

Proves `src/signalbudget/`, `tests/`, and `integration_tests/` do not import
DetFuzz code.

## Latest VM Evidence

`evidence/detfuzz-signalbudget-results-20260723-212216-posix.zip`

```text
SHA256 2570ce74dd2d49d4af708b7a1153278c2aa01622e0b6fd1896c0787a3ceb4d4d
suite_id 4ddc2989-4c84-49fe-801e-996c67a5702f
suite_status COMPLETED
evidence_files_checked 63
evidence_hashes_verified true
```

The archive includes the raw Windows VM suite, evidence manifest, per-case
evidence, calibration data, and generated SignalBudget outputs. The M1 case
uses the explicitly reported legacy preliminary-classification compatibility
described in `docs/data-contract.md`.

## Pricing Evidence

`pricing/microsoft_sentinel_eastus_2026-07-23.yaml`

Stores the Microsoft Sentinel East US profile with retrieval, effective-date,
source, and freshness metadata.

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

Machine-readable Pareto result regenerated from the latest VM suite.

`artifacts/phase-9/pareto-analysis.md`

Human-readable Pareto report.

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
tradeoffs regenerated from the latest VM suite.

`artifacts/phase-10/tradeoff-explanations.md`

Human-readable tradeoff report.

Removing `sysmon_process_create` loses the validated rule
`d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62`
(`detfuzz-v0-powershell-encoded-command`).

## Verification Evidence

`tests/` contains unit and regression tests.

`integration_tests/` verifies exported DetFuzz evidence is accepted by the
SignalBudget strict contract without importing DetFuzz code.

`.github/workflows/ci.yml` builds and installs the wheel, runs the unit and
integration suites, lints, and type-checks on Python 3.11.
