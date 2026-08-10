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
- Refuses to count a detection as validated unless hash-verified DetFuzz
  evidence proves it fired. `pareto-analysis` and `explain-tradeoffs` will not
  run at all without a verified suite artifact.

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
Expand-Archive evidence\detfuzz-signalbudget-results-20260723-212216-posix.zip -DestinationPath build\v1-evidence
$run = 'build\v1-evidence\4ddc2989-4c84-49fe-801e-996c67a5702f'
python -m signalbudget.cli validate-detfuzz --path "$run\reports\suite-report.json" --evidence-root "$run\evidence" --require-suite-contract
python -m signalbudget.cli pareto-analysis --output-dir artifacts\phase-9 --detfuzz-result "$run\reports\suite-report.json" --detfuzz-evidence-root "$run\evidence"
python -m signalbudget.cli explain-tradeoffs --output-dir artifacts\phase-10 --detfuzz-result "$run\reports\suite-report.json" --detfuzz-evidence-root "$run\evidence"
```

The same sequence on macOS or Linux:

```bash
export PYTHONPATH=src
python -m unittest discover -s tests
python -m signalbudget.cli summarize

mkdir -p build/v1-evidence
unzip -q evidence/detfuzz-signalbudget-results-20260723-212216-posix.zip -d build/v1-evidence
run=build/v1-evidence/4ddc2989-4c84-49fe-801e-996c67a5702f
python -m signalbudget.cli validate-detfuzz --path "$run/reports/suite-report.json" --evidence-root "$run/evidence" --require-suite-contract
python -m signalbudget.cli pareto-analysis --output-dir artifacts/phase-9 --detfuzz-result "$run/reports/suite-report.json" --detfuzz-evidence-root "$run/evidence"
python -m signalbudget.cli explain-tradeoffs --output-dir artifacts/phase-10 --detfuzz-result "$run/reports/suite-report.json" --detfuzz-evidence-root "$run/evidence"
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
configuration_count: 8
complete_cost_configuration_count: 8
partial_cost_configuration_count: 0
non_dominated: 7
dominated: windows_security_logon
```

`pricing_status` is deliberately not pinned here. It is computed at run time from
`retrieved_at` and `max_age_days` in the pricing profile, so a profile retrieved
on 2026-07-23 with a 90-day budget reports `PRICING_FRESH` until roughly
2026-10-21 and `PRICING_STALE` afterwards. A stale profile still produces a full
analysis; the reports simply carry the `PRICING_STALE` label so the estimate is
never mistaken for current pricing. Pass `--fail-on-stale-pricing` to
`pareto-analysis` or `explain-tradeoffs` to turn that label into a hard failure
instead.

Because the status is a run-time value, a committed report is a snapshot of it.
Both Markdown reports therefore print the profile's `retrieved_at` and
`max_age_days` beneath the status line, so a reader can date the claim without
re-running the tool. Those two lines come from the stored profile rather than the
clock, which is what keeps the committed reports byte-stable for the CI diff.

`windows_security_logon` is dominated by `powershell_script_block` in this lab
measurement because both provide one investigation question and zero
DetFuzz-validated detections, while PowerShell Script Block is cheaper in the
observed 24-hour VM window.

This is a narrow lab finding, not a production-wide claim. Production logon
volume can change that tradeoff.

## Reading The Cost Numbers

Volumes were measured on a single Windows VM, so every cost in this repository
is **per endpoint per month**. The frontier spans roughly $0.003 to $0.30 in
those units. Fleet cost is that figure multiplied by endpoint count:

```text
full three-source collection   $0.30219411 x 5,000 endpoints x 12 = ~$18,000/year
powershell script block only   $0.00318630 x 5,000 endpoints x 12 = ~$191/year
```

Those illustrative totals are arithmetic on lab measurements, not a production
forecast. Two limits apply to every figure:

- Sizing uses exported event XML as a proxy for billable ingestion volume, and
  is labeled `XML_EXPORT_SIZE_PROXY` throughout. Real ingestion size differs.
- The 24-hour measurement window included DetFuzz test execution, so it is not
  a clean idle baseline. The measurement file records this.

The two ratios the frontier supports as telemetry KPIs are **validated
detections per dollar per month** and **investigation questions answerable per
dollar per month**. Both fall directly out of the per-configuration counts and
costs in `artifacts/phase-9/pareto-analysis.json`, and both are what the
source-removal report in `artifacts/phase-10` prices when a source is dropped.

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

## Design Notes

**Zero runtime dependencies.** The installed package imports nothing outside the
Python standard library; `mypy` and `ruff` are development extras only. The
catalogs use a small, fixed YAML subset, so `loaders.load_restricted_yaml`
parses exactly that subset and raises on anything else rather than pulling in a
general-purpose YAML parser. Nothing to audit, patch, or pin at runtime.

**BOM tolerance is deliberate.** DetFuzz artifacts are PowerShell-generated and
carry a UTF-8 BOM, so every artifact read uses `utf-8-sig`. Test fixtures keep
their BOMs on purpose to hold that behaviour under test, and
`tests/fixtures/evidence/**` is pinned to CRLF in `.gitattributes` because those
bytes are covered by recorded SHA-256 hashes.

**Exit codes.** Every command returns `0` on success and `2` on failure.
Contract violations, malformed artifacts, missing files, and stale-pricing
rejections print a single-line message to stderr instead of a traceback:

```text
signalbudget: error: evidence hash mismatch for B0/case-record.json
```

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

Continuous integration builds a wheel, installs it, and runs the CLI from
outside the repository to prove that. It then verifies the evidence archive
checksum, regenerates both reports from the committed evidence, and diffs them
against `artifacts/` so the published numbers cannot drift from the evidence
that produced them. A final step corrupts an evidence file and asserts that
validation rejects it.

Extracting the evidence archive anywhere under `evidence/` is ignored by git;
only the `.zip` and its `.sha256.txt` are tracked.

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

## Status

SignalBudget v1 is complete and reproducible from a fresh clone. The committed
evidence archive revalidates against its checksum, all 63 evidence files pass
hash verification, and both reports regenerate from that evidence — CI diffs the
regenerated Markdown against the committed copies on every push, and separately
asserts that corrupted evidence is rejected.

Scope is deliberately narrow: three Windows log sources, one DetFuzz-validated
detection, and costs derived from a 24-hour lab VM window. What that supports and
what it does not is set out in `docs/limitations-and-future-work.md`.

Phase numbering in `docs/` continues DetFuzz's sequence; SignalBudget's own work
begins at phase 8.

## License

MIT. See `LICENSE`.

The committed evidence archive is lab output and carries only neutral
identifiers — host `DetFuzz-Win11-Lab`, account path `C:\Users\detfuzz-lab`.
Microsoft Sentinel prices in `pricing/` are retail figures recorded from the
Azure Retail Prices API on the date stored in the profile; they are reproduced
as measured input, not as a price list.
