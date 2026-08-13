# Changelog

Notable changes per release. Dates are ISO-8601.

## Unreleased

Maintenance only. No runtime package code, catalog, pricing, or report output is
affected, so the v1.2.0 artifacts remain the current release.

- Corrected the freshness window in four documents that still described age as a
  function of `retrieved_at` alone. `docs/phase-10-summary.md` was the one that
  mattered: under a heading reading "Current Result" it pinned `PRICING_FRESH`
  until 2026-10-21, which the verification date moved to 2026-11-08.
- Replaced every em and en dash in the prose files with a plain hyphen.
  `tests/fixtures/` was left untouched; those bytes are pinned by recorded
  SHA-256 hashes.
- Removed the calendar dependency from the tradeoff-report pricing-status test,
  so the suite continues to pass when a correctly aged profile becomes stale.
- Corrected the evidence archive entry count and generated-report SHA-256 values
  in `docs/phase-11-vm-validation.md`, with regression tests that keep those
  claims synchronized with the committed files.
- CI now compares normalized JSON reports as well as Markdown, excluding only
  the pricing-freshness fields that legitimately change with the run date.

## 1.2.0 - 2026-08-10

### Changed

- Pricing freshness is now measured from the later of `retrieved_at` and
  `verified_at` rather than from `retrieved_at` alone. Re-querying the source
  API and finding the meters unchanged is current evidence that the stored
  prices still hold, so a profile carrying such a check is not stale merely
  because the original download was long ago. `verified_at` remains optional and
  the behaviour is unchanged without it. Re-verification defers staleness by
  `max_age_days` from the verification date; it does not make a profile
  permanently fresh.
- `pricing_freshness` output gained `verified_at` and `freshness_basis`, and the
  Markdown reports print the verification date under the status line.

### Data

- All three stored meters re-queried from the Azure Retail Prices API on
  2026-08-10 and confirmed unchanged - Analytics $4.30/GB, Basic $0.50/GB,
  Auxiliary $0.05/GB, matching on price, unit, effective date, and meter naming.
  `verified_at` moved to 2026-08-10, which shifts the stale date from
  2026-10-21 to roughly 2026-11-08. No price value changed.
- `docs/pricing-assumptions.md` gained a verification log and an inventory of
  the 21 eastus Sentinel meters the profile deliberately does not model, most
  significantly the commitment tiers - which are why the stored pay-as-you-go
  rate is an upper bound on ingestion cost at fleet scale.

## 1.1.0 - 2026-08-10

Everything below landed on `main` after the `v1.0.0` tag was cut, so the tagged
1.0.0 archive contains none of it. The tag was left where it is; this release
supersedes it.

### Added

- MIT license, declared through PEP 639 metadata so `LICENSE` also ships inside
  the built wheel.
- `--fail-on-stale-pricing` on `explain-tradeoffs`, matching `pareto-analysis`,
  so both analysis commands share one pricing-freshness policy.
- Both Markdown reports print the pricing profile's `retrieved_at` and
  `max_age_days` under the status line, so a committed report can be dated
  without re-running the tool.

### Fixed

- CLI failures printed a raw Python traceback and still exited `0`. Contract
  violations, malformed JSON, missing files, and stale-pricing rejections now
  produce a single line on stderr and exit `2`.
- `enumerate-configurations` emitted validated-detection counts without ever
  consulting evidence. It now accepts `--detfuzz-result` and reports the
  contract summary alongside the counts.
- The restricted YAML loader mis-parsed quoted inline lists, splitting on commas
  inside quoted strings.
- The evidence archive stored backslash-separated member names, which Python's
  `zipfile` extracted as literal flat filenames on macOS and Linux. Regenerated
  with portable `/` separators.
- Stray UTF-8 BOMs removed from seven source and documentation files. The BOMs
  under `tests/fixtures/` are deliberate - they keep the `utf-8-sig` handling
  under test and are pinned by recorded hashes.
- Documentation pinned `PRICING_FRESH` as though it were permanent. It is
  computed from profile age and flips to `PRICING_STALE` around 2026-10-21.

### Changed

- SignalBudget no longer depends on DetFuzz code in any form. It consumes
  exported JSON artifacts only, and a test fails the build on any `detfuzz.*`
  import.
- CI verifies the evidence archive checksum, regenerates both reports from the
  committed evidence, and diffs them against every committed copy - `artifacts/`
  and the duplicates under `evidence/`. A further step corrupts an evidence file
  and asserts the validator rejects it.
- Minimum setuptools raised to 77 for SPDX license metadata.

## 1.0.0 - 2026-07-23

Initial release: three Windows log sources, cost estimates from 24-hour lab VM
measurements priced against a stored Microsoft Sentinel profile, Pareto analysis
across cost, DetFuzz-validated detection coverage, and investigation utility,
and hash-verified DetFuzz evidence as the gate on the word "validated".
