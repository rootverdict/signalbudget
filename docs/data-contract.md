# DetFuzz to SignalBudget Data Contract

SignalBudget reads DetFuzz exported JSON artifacts. It does not import DetFuzz
Python modules.

## Schema

The contract lives at:

```text
contracts/detfuzz_result_schema.json
```

The schema is based on real Phase 7 `benign-results.json` evidence and the real
Phase 6 B0 suite report shape.

## Required Fields

```text
schema_version
suite_id
cases[]
cases[].case_id
cases[].classification
```

## Optional Fields Used When Present

```text
suite_status
environment.rule_id
environment.telemetry
cases[].telemetry_valid
cases[].detection_matched
cases[].marker_valid
cases[].detection_reason
cases[].telemetry_reason
```

Unsupported `schema_version` values are rejected explicitly.
