# Limitations And Future Work

## Current Limitations

`Lab volume estimates are not production forecasts`

The current costs come from 24-hour measurements on a lightly used Windows lab
VM. They are useful for demonstrating the workflow, but they should not be used
as production billing forecasts.

`Only three log sources are modeled`

SignalBudget v1 includes:

```text
sysmon_process_create
powershell_script_block
windows_security_logon
```

It does not yet model endpoint detection products, cloud identity logs, DNS,
proxy, EDR process lineage, or SIEM retention tiers beyond the stored Microsoft
Sentinel pricing profile.

`Only one detection is DetFuzz-validated`

The DetFuzz-validated detection is:

```text
d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62
```

PowerShell Script Block and Windows Security detections are catalog-declared but
not validated by DetFuzz evidence yet.

`The Pareto result depends on catalog scope`

The current Pareto frontier is correct for the three-source v1 catalog and the
current investigation-question set. Adding new detections, questions, or log
sources can change the frontier.

`The dominated Security-only result is narrow`

`windows_security_logon` is dominated by `powershell_script_block` in the current
lab data because both provide one investigation question and zero
DetFuzz-validated detections, while PowerShell Script Block is cheaper. This is
not a general claim that Windows Security logging is expensive in all
environments.

## Future Work

`Add more validated detections`

Run DetFuzz-style validation for:

```text
powershell_script_block_encoded_activity
windows_failed_logon_context
```

Then update `dependency_status` when real evidence exists.

`Add more telemetry sources`

Potential sources:

```text
Microsoft Defender for Endpoint
Entra ID sign-in logs
DNS logs
Proxy logs
Cloud audit logs
```

`Add production sampling mode`

Support longer measurement windows and multiple environment profiles, such as:

```text
idle_lab
active_lab
small_business
enterprise_endpoint
```

`Add uncertainty ranges`

Represent cost as a range when volume is sampled from a short window.

`DetFuzz v0.2 parent-process mutation`

Parent-process mutation was intentionally deferred because it changes telemetry
semantics. It remains a strong DetFuzz v0.2 candidate.
