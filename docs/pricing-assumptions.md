# Pricing Assumptions

Phase 8 uses Microsoft Sentinel pricing from the official Azure Retail Prices
API.

## Profile

```text
pricing/microsoft_sentinel_eastus_2026-07-21.yaml
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

## Boundary

Prices are Microsoft retail prices in USD. Actual customer charges can differ
because of agreements, taxes, currency exchange, purchase date, free trials, or
commitment plans.

## Current Volume Boundary

Only `sysmon_process_create` has a Phase 8 byte-size cost estimate. It uses a
24-hour VM event count and the first 100 exported Sysmon XML events for average
event size. The measurement window includes DetFuzz test execution activity, so
it is a lab estimate, not a pure idle baseline or production bill forecast.
