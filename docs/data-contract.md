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

SignalBudget applies this schema at runtime using its standard-library schema
subset validator. The schema describes the base import contract accepted by
`validate-detfuzz`; strict Pareto and tradeoff analysis adds the semantic suite
requirements documented below.

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

## Strict Analysis Contract

`pareto-analysis`, `explain-tradeoffs`, and
`validate-detfuzz --require-suite-contract` additionally require:

```text
suite_status: COMPLETED
environment.rule_id: d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62
exactly B0, M1-M5, NC1, and B1
valid markers, telemetry, and executable identity for every case
an evidence manifest with every required per-case artifact
all manifest paths contained by the evidence root
matching file sizes and SHA-256 hashes
case summaries matching case-record, marker, telemetry, executable-identity,
and detection-result evidence
```

This two-level contract allows partial and benign DetFuzz reports to be
inspected without granting them validated detection coverage.
