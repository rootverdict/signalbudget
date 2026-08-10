# Changelog

Notable changes per release. Dates are ISO-8601.

## 1.1.0 — 2026-08-10

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
  under `tests/fixtures/` are deliberate — they keep the `utf-8-sig` handling
  under test and are pinned by recorded hashes.
- Documentation pinned `PRICING_FRESH` as though it were permanent. It is
  computed from profile age and flips to `PRICING_STALE` around 2026-10-21.

### Changed

- SignalBudget no longer depends on DetFuzz code in any form. It consumes
  exported JSON artifacts only, and a test fails the build on any `detfuzz.*`
  import.
- CI verifies the evidence archive checksum, regenerates both reports from the
  committed evidence, and diffs them against every committed copy — `artifacts/`
  and the duplicates under `evidence/`. A further step corrupts an evidence file
  and asserts the validator rejects it.
- Minimum setuptools raised to 77 for SPDX license metadata.

## 1.0.0 — 2026-07-23

Initial release: three Windows log sources, cost estimates from 24-hour lab VM
measurements priced against a stored Microsoft Sentinel profile, Pareto analysis
across cost, DetFuzz-validated detection coverage, and investigation utility,
and hash-verified DetFuzz evidence as the gate on the word "validated".
