# SignalBudget v1 Scope

SignalBudget v1 is a command-line, lab-backed security telemetry planning
tool. This document is the release boundary: behavior listed here is required
for v1; behavior listed under v2 is intentionally deferred and is not a v1
defect.

## Included In v1

- A Python 3.11+ command-line package with these commands:
  - `summarize`
  - `validate-detfuzz`
  - `enumerate-configurations`
  - `pareto-analysis`
  - `explain-tradeoffs`
- Exactly three Windows telemetry sources:
  - Sysmon Process Create, Event ID 1
  - PowerShell Script Block Logging, Event ID 4104
  - Windows Security logon events, Event IDs 4624 and 4625
- One Microsoft Sentinel East US retail-pricing profile.
- Lab-derived 24-hour volume measurements for all three sources.
- Enumeration of all eight source combinations.
- Cost, telemetry readiness, DetFuzz-validated detection coverage, and
  investigation-question coverage for each combination.
- Pareto-frontier analysis without arbitrary metric weights.
- Source-removal and frontier tradeoff explanations.
- Pricing-freshness reporting.
- One DetFuzz-validated detection and two catalog-declared, unvalidated
  detections.
- Strict DetFuzz suite and evidence-manifest validation, including SHA-256,
  file size, required evidence, semantic cross-checks, and safe relative paths.
- A narrowly identified compatibility path for older DetFuzz v0 evidence that
  records `CANDIDATE_VALID_BYPASS` before the closing baseline finalizes the
  report classification as `VALID_BYPASS`.
- JSON and Markdown reports.
- Wheel packaging with all catalogs, contracts, measurements, and pricing data.
- Unit tests, cross-project integration, linting, type checking, and CI.
- Explicit warnings that lab-derived costs are not production forecasts.

## Definition Of Done

V1 is complete when every included capability is implemented, the unit and
cross-project integration suites pass, Ruff and Mypy pass, a wheel installs and
runs outside the repository, strict validation succeeds against the
repository-local evidence archive, and generated reports agree with that
archive.

## Deferred To v2

- DetFuzz validation for the PowerShell Script Block and Windows Security
  detections.
- Additional endpoint, identity, DNS, proxy, EDR, and cloud telemetry sources.
- Multiple environments, regions, pricing profiles, and retention tiers.
- Longer or automated production sampling.
- Cost uncertainty ranges.
- Larger-catalog performance work.
- Parent-process mutation support through a future DetFuzz contract.

## Not Promised

- A web, desktop, or public API interface.
- Accounts, authentication, or database storage.
- Direct modification of production logging or Sentinel configuration.
- Guaranteed customer billing estimates or production-wide recommendations.
- Correctness of DetFuzz internals beyond the exported v1 data contract.
