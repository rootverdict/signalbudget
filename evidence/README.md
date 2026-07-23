# SignalBudget v1 Evidence Index

The latest local evidence package is:

```text
detfuzz-signalbudget-results-20260723-212216.zip
SHA256 6598a2e5e5fa9c71c5d21948ccea35ea812088a720a6100197c513d034ed034a
```

It contains the completed DetFuzz Windows VM suite
`4ddc2989-4c84-49fe-801e-996c67a5702f`, its evidence manifest, 63 hashed
evidence files, calibration results, and the generated SignalBudget reports.

The DetFuzz producer used for this run retained
`CANDIDATE_VALID_BYPASS` in the hashed M1 case record before the closing B1
baseline finalized the suite-report classification as `VALID_BYPASS`.
SignalBudget v1 recognizes only this exact preliminary-to-final transition and
reports it as:

```text
legacy_preliminary_classifications_accepted: M1
```

Extract and validate the archive from the repository root:

```powershell
Expand-Archive evidence\detfuzz-signalbudget-results-20260723-212216.zip -DestinationPath build\v1-evidence
$run = 'build\v1-evidence\4ddc2989-4c84-49fe-801e-996c67a5702f'
python -m signalbudget.cli validate-detfuzz `
  --path "$run\reports\suite-report.json" `
  --evidence-root "$run\evidence" `
  --require-suite-contract
```

Expected result:

```text
suite_status: COMPLETED
evidence_files_checked: 63
evidence_hashes_verified: true
validated_rule_ids: d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62
legacy_preliminary_classifications_accepted: M1
```

## Zip Portability Note

The current archive was verified with Python's `zipfile` module and uses
portable `/` member separators, so scripted extraction creates real nested
directories such as:

```text
4ddc2989-4c84-49fe-801e-996c67a5702f/reports/suite-report.json
```

When regenerating evidence packages on Windows, keep zip member names in this
portable form. Backslash-separated member names can be extracted by Python as
literal flat filenames on macOS/Linux, even when some unzip tools repair them
with a warning.

The human-readable reports in this directory are regenerated from that suite:

```text
pareto-analysis.md
tradeoff-explanations.md
```

The cost estimates remain lab-derived from a 24-hour Windows VM measurement
and are not production forecasts.
