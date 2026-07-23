# Demo Script

This is a short walkthrough for an interview or portfolio review.

## 1. Open With The Problem

SignalBudget asks:

```text
If telemetry costs money, which log sources should a SOC keep, and what does it
lose when it removes one?
```

The point is not to choose the cheapest logs blindly. The point is to make
cost, validated detection coverage, and investigation utility visible together.

## 2. Show The DetFuzz Connection

DetFuzz generated real Windows/Sysmon evidence for an encoded PowerShell rule.
SignalBudget consumes DetFuzz JSON through a schema:

```powershell
$env:PYTHONPATH='src'
python -m signalbudget.cli validate-detfuzz --path tests\fixtures\benign-results.json
python -m signalbudget.cli validate-detfuzz --path C:\DetFuzz\portfolio-v0\runs\dc017824-0d4e-41d0-9d32-610b410accb0\reports\suite-report.json --evidence-root C:\DetFuzz\portfolio-v0\runs\dc017824-0d4e-41d0-9d32-610b410accb0\evidence --require-suite-contract
```

Emphasize:

```text
The deployable SignalBudget package imports exported DetFuzz data, not
`detfuzz.*` code.
```

For the live handoff demo, use DetFuzz's canonical report artifact:

```powershell
python -m signalbudget.cli validate-detfuzz --path C:\DetFuzz\runs\<suite-id>\reports\suite-report.json --evidence-root C:\DetFuzz\runs\<suite-id>\evidence --require-suite-contract
```

## 3. Show The Catalog

Open:

```text
catalog/log_sources.yaml
catalog/detection_dependencies.yaml
catalog/investigation_questions.yaml
```

Explain that v0 uses three sources only:

```text
Sysmon Process Create
PowerShell Script Block
Windows Security Logon
```

## 4. Run The Tests

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

Expected:

```text
OK
```

Point out the boundary test:

```text
tests/test_no_detfuzz_imports.py
```

## 5. Generate The Pareto Analysis

```powershell
python -m signalbudget.cli pareto-analysis --output-dir artifacts\phase-9 --detfuzz-result C:\DetFuzz\portfolio-v0\runs\dc017824-0d4e-41d0-9d32-610b410accb0\reports\suite-report.json --detfuzz-evidence-root C:\DetFuzz\portfolio-v0\runs\dc017824-0d4e-41d0-9d32-610b410accb0\evidence
```

Open:

```text
artifacts/phase-9/pareto-analysis.md
```

Key result:

```text
8 configurations
8 complete-cost configurations
0 partial-cost configurations
windows_security_logon is dominated
```

## 6. Explain The Dominated Source

Say:

```text
In this lab VM window, windows_security_logon alone is dominated by
powershell_script_block because both provide one investigation question and zero
DetFuzz-validated detections, while PowerShell Script Block is cheaper.
```

Then immediately qualify it:

```text
This is a lab-volume finding, not a general production claim.
```

## 7. Generate Tradeoff Explanations

```powershell
python -m signalbudget.cli explain-tradeoffs --output-dir artifacts\phase-10 --detfuzz-result C:\DetFuzz\portfolio-v0\runs\dc017824-0d4e-41d0-9d32-610b410accb0\reports\suite-report.json --detfuzz-evidence-root C:\DetFuzz\portfolio-v0\runs\dc017824-0d4e-41d0-9d32-610b410accb0\evidence
```

Open:

```text
artifacts/phase-10/tradeoff-explanations.md
```

Show:

```text
pricing_status: PRICING_FRESH
remove sysmon_process_create -> lose DetFuzz validated detection
baseline: none
frontier transitions in non-decreasing cost order
```

## 8. Close With The Honest Boundary

End with:

```text
SignalBudget demonstrates a data-driven method for telemetry planning. The v0
numbers are lab-derived from a 24-hour VM window, so they prove the workflow and
not a production bill forecast.
```
