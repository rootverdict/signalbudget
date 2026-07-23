# SignalBudget v1

SignalBudget is a cost-aware security telemetry planning tool. It answers a
practical blue-team question:

```text
Which log sources are worth keeping when cost, detection coverage, and
investigation utility all matter?
```

The project is paired with DetFuzz evidence, not DetFuzz code. DetFuzz produces
real Windows/Sysmon evidence for one validated detection rule; SignalBudget
consumes the exported JSON artifacts through a versioned data contract and
keeps the other catalog detections clearly labeled as declared but not
DetFuzz-validated. SignalBudget does not import `detfuzz.*` code.

## What It Does

- Defines a three-source telemetry catalog:
  - Sysmon Process Create, Event ID 1
  - PowerShell Script Block Logging, Event ID 4104
  - Windows Security logon events, Event IDs 4624 and 4625
- Loads real Microsoft Sentinel pricing data.
- Tracks pricing freshness with `PRICING_FRESH` / `PRICING_STALE`.
- Uses 24-hour lab VM volume measurements to estimate monthly cost.
- Enumerates all eight source combinations.
- Builds a Pareto frontier over:
  - lower monthly cost,
  - higher validated detection coverage,
  - higher investigation-question coverage.
- Explains what detections and questions are lost when each source is removed.

## Quick Check

Run from the SignalBudget project root:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
python -m signalbudget.cli summarize
python -m signalbudget.cli validate-detfuzz --path tests\fixtures\benign-results.json
```

Those fixture commands are local smoke tests. The final portfolio artifacts
under `artifacts/phase-9` and `artifacts/phase-10` were regenerated from the
repository-local DetFuzz VM evidence archive. Extract it once:

```powershell
Expand-Archive evidence\detfuzz-signalbudget-results-20260723-212216.zip -DestinationPath build\v1-evidence
$run = 'build\v1-evidence\4ddc2989-4c84-49fe-801e-996c67a5702f'
python -m signalbudget.cli validate-detfuzz --path "$run\reports\suite-report.json" --evidence-root "$run\evidence" --require-suite-contract
python -m signalbudget.cli pareto-analysis --output-dir artifacts\phase-9 --detfuzz-result "$run\reports\suite-report.json" --detfuzz-evidence-root "$run\evidence"
python -m signalbudget.cli explain-tradeoffs --output-dir artifacts\phase-10 --detfuzz-result "$run\reports\suite-report.json" --detfuzz-evidence-root "$run\evidence"
```

Run the standalone exported-evidence contract test:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s integration_tests
```

Expected test result:

```text
OK
```

## Main Outputs

- `artifacts/phase-9/pareto-analysis.json`
- `artifacts/phase-9/pareto-analysis.md`
- `artifacts/phase-10/tradeoff-explanations.json`
- `artifacts/phase-10/tradeoff-explanations.md`
- `evidence/README.md`

The latest VM evidence archive is stored under `evidence/`, together with
its SHA-256 checksum. A fresh clone can revalidate all 63 evidence files and
regenerate the SignalBudget reports locally.

Current result:

```text
pricing_status: PRICING_FRESH
configuration_count: 8
complete_cost_configuration_count: 8
partial_cost_configuration_count: 0
dominated: windows_security_logon
```

`windows_security_logon` is dominated by `powershell_script_block` in this lab
measurement because both provide one investigation question and zero
DetFuzz-validated detections, while PowerShell Script Block is cheaper in the
observed 24-hour VM window.

This is a narrow lab finding, not a production-wide claim. Production logon
volume can change that tradeoff.

## Evidence Boundary

SignalBudget uses real artifacts, but it labels their scope carefully:

- DetFuzz evidence artifacts are exported JSON files, not imported DetFuzz code.
- Pareto and tradeoff analysis require a full DetFuzz suite artifact with
  verified evidence-manifest hashes before granting validated coverage.
- Microsoft Sentinel pricing is stored in versioned YAML with freshness fields.
- Cost estimates are lab-derived from 24-hour VM measurements and are not
  production forecasts; XML-derived byte sizing is labeled as a proxy estimate.
- Only the Sysmon encoded PowerShell detection is DetFuzz-validated in v1.
- PowerShell Script Block and Windows Security detections are catalog-declared,
  not DetFuzz-validated.

Strict evidence verification requires an explicit `--evidence-root`.
SignalBudget never follows the absolute root embedded in an imported manifest,
and rejects absolute, traversal, duplicate, missing, incorrectly sized, or
hash-mismatched evidence entries.

## Release Verification

```powershell
python -m pip install -c constraints.txt -e ".[dev]"
python -m ruff check src tests integration_tests
python -m mypy src
python -m unittest discover -s tests -v
python -m unittest discover -s integration_tests -v
python -m signalbudget.cli summarize
```

Catalog, measurement, pricing, and contract files are included in the Python
package, so the installed CLI does not depend on the repository checkout.

## Documentation

- `docs/v1-scope.md`
- `docs/architecture.md`
- `docs/demo-script.md`
- `docs/evidence-index.md`
- `docs/limitations-and-future-work.md`
- `docs/phase-11-vm-validation.md`
- `docs/phase-8-summary.md`
- `docs/phase-9-summary.md`
- `docs/phase-10-summary.md`
- `docs/phase-11-summary.md`

## Final Status

```text
SignalBudget Phase 8: catalog, contract, pricing
SignalBudget Phase 9: complete Pareto analysis
SignalBudget Phase 10: freshness and loss explanations
SignalBudget Phase 11: documentation and demo package
SignalBudget v1: locally complete
```
