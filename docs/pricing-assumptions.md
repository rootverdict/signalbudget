# Pricing Assumptions

Phase 8 uses Microsoft Sentinel pricing from the official Azure Retail Prices
API.

## Profile

```text
pricing/microsoft_sentinel_eastus_2026-07-23.yaml
```

## Freshness Fields

The profile includes:

```text
retrieved_at
effective_date
max_age_days
source_url
```

The filename is only a human-readable anchor. Code must use fields inside the
profile when checking freshness.

`retrieved_at` is when the prices were downloaded. `verified_at` is the last
time they were re-queried from `source_url` and found unchanged. Age is measured
from whichever is later, because a re-query that returns identical meters is
current evidence that the stored prices still hold, and the profile should not
be called stale for the age of its original download alone. `verified_at` is
optional; without it, age is measured from retrieval.

Re-verification defers staleness by `max_age_days` from the verification date —
it does not make a profile permanently fresh.

## Verification Log

```text
2026-07-23  retrieved
2026-08-10  re-verified, all three meters unchanged
```

The 2026-08-10 check re-queried all three meter IDs and compared `retailPrice`,
`unitPrice`, `unitOfMeasure`, `effectiveStartDate`, `meterName`, `skuName`, and
`serviceName`. Every field matched. The Analytics meter that drives the cost
numbers still carries `effectiveStartDate: 2023-07-01T00:00:00Z`.

`retrieved_at`, `verified_at`, and `max_age_days` are also printed under the
`Pricing status:` line of both generated Markdown reports. A committed report records the status
as of the moment it was generated, and those two fields are what let a reader
tell whether that status still holds. They are read from the profile rather than
the clock, so regenerating the reports on a later date changes only the status
line itself.

## Boundary

Prices are Microsoft retail prices in USD. Actual customer charges can differ
because of agreements, taxes, currency exchange, purchase date, free trials, or
commitment plans.

The Analytics entry is the Microsoft Sentinel simplified-plan combined
ingestion-and-analysis meter. Basic and Auxiliary entries are Azure Monitor
data-ingestion meters. Query-analysis meters are intentionally excluded because
their cost depends on query scan volume, not ingested source volume.

Note that Sentinel publishes its own `Basic Logs Analysis` meter at a different
rate from the Azure Monitor `Basic Logs Data Ingestion` meter stored here. The
ingestion meter is the one that matches how this tool models cost, which is
per gigabyte of source volume collected.

## Unmodeled Meters

The eastus Sentinel service publishes 24 meters. This profile stores 3. The
remainder are out of scope for v1 rather than missing:

```text
commitment tier capacity reservations   50 GB/day through 50000 GB/day
data lake ingestion, storage, query     added 2025-10-01
data processing                         added 2025-10-01
advanced data insights                  hourly, added 2025-10-01
graph                                   hourly, added 2026-04-01
free benefit and free trial analysis    zero-rate
```

The commitment tiers matter most for interpreting the per-endpoint figures. Any
fleet large enough for the ~$18k/year framing in the README would be priced on a
tier rather than pay-as-you-go, and the effective per-gigabyte rate on a tier is
below the $4.30 pay-as-you-go rate used here. The stored estimate is therefore
an upper bound on ingestion cost at scale, not a forecast.

## Current Volume Boundary

All three sources have 24-hour byte-size proxy estimates. Sysmon and Windows
Security use the first 100 exported XML events for average event size;
PowerShell Script Block uses all nine events observed in its measurement
window. The windows include DetFuzz test execution activity, so these are lab
estimates, not pure idle baselines or production bill forecasts.
