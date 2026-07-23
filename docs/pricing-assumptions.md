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

## Boundary

Prices are Microsoft retail prices in USD. Actual customer charges can differ
because of agreements, taxes, currency exchange, purchase date, free trials, or
commitment plans.

The Analytics entry is the Microsoft Sentinel simplified-plan combined
ingestion-and-analysis meter. Basic and Auxiliary entries are Azure Monitor
data-ingestion meters. Query-analysis meters are intentionally excluded because
their cost depends on query scan volume, not ingested source volume.

## Current Volume Boundary

All three sources have 24-hour byte-size proxy estimates. Sysmon and Windows
Security use the first 100 exported XML events for average event size;
PowerShell Script Block uses all nine events observed in its measurement
window. The windows include DetFuzz test execution activity, so these are lab
estimates, not pure idle baselines or production bill forecasts.
