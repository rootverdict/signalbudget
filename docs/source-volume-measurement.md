# Source Volume Measurement

SignalBudget v1 includes 24-hour lab VM measurements for all three sources.
These measurements make the Phase 9 Pareto frontier complete, but they remain
lab estimates rather than production forecasts.

## Current Included Sample

```text
source: sysmon_process_create
measurement_status: lab_24h_measurement
events_observed: 898
sample_events_exported: 100
sample_xml_bytes_observed: 215745
bytes_per_event_observed: 2157.45
estimated_events_per_day: 898
estimated_gb_per_day: 0.0019374
estimated_monthly_proxy_cost_usd: 0.2499246
cost_estimate_kind: XML_EXPORT_SIZE_PROXY
```

Additional measured sources:

```text
powershell_script_block:
  events_observed: 9
  sample_xml_bytes_observed: 24700
  estimated_monthly_proxy_cost_usd: 0.0031863

windows_security_logon:
  events_observed: 208
  sample_xml_bytes_observed: 182928
  estimated_monthly_proxy_cost_usd: 0.04908321
```

The measurement windows include DetFuzz test execution activity. They are useful
for Phase 9 cost math, but they are not pure idle baselines or production
forecasts.

## Suggested 24-Hour VM Commands

Run in Administrator PowerShell in the Windows VM:

```powershell
$since = (Get-Date).AddHours(-24)

$sysmon = Get-WinEvent -FilterHashtable @{
  LogName = 'Microsoft-Windows-Sysmon/Operational'
  Id = 1
  StartTime = $since
}

$scriptBlock = Get-WinEvent -FilterHashtable @{
  LogName = 'Microsoft-Windows-PowerShell/Operational'
  Id = 4104
  StartTime = $since
} -ErrorAction SilentlyContinue

$security = Get-WinEvent -FilterHashtable @{
  LogName = 'Security'
  Id = 4624,4625
  StartTime = $since
} -ErrorAction SilentlyContinue

[ordered]@{
  measured_at_utc = (Get-Date).ToUniversalTime().ToString('o')
  window_hours = 24
  sysmon_process_create_events = @($sysmon).Count
  powershell_script_block_events = @($scriptBlock).Count
  windows_security_logon_events = @($security).Count
} | ConvertTo-Json -Depth 4
```

For proxy byte size, export representative events and measure the resulting XML.
This is useful for the lab comparison, but it is not the same as Sentinel
`_BilledSize`:

```powershell
New-Item -ItemType Directory -Force -Path C:\DetFuzz\volume | Out-Null
$sysmon | Select-Object -First 100 | ForEach-Object { $_.ToXml() } |
  Set-Content -LiteralPath C:\DetFuzz\volume\sysmon-process-create-sample.xml -Encoding UTF8

$scriptBlock | Select-Object -First 100 | ForEach-Object { $_.ToXml() } |
  Set-Content -LiteralPath C:\DetFuzz\volume\powershell-script-block-sample.xml -Encoding UTF8

$security | Select-Object -First 100 | ForEach-Object { $_.ToXml() } |
  Set-Content -LiteralPath C:\DetFuzz\volume\windows-security-logon-sample.xml -Encoding UTF8

Get-Item C:\DetFuzz\volume\sysmon-process-create-sample.xml,
         C:\DetFuzz\volume\powershell-script-block-sample.xml,
         C:\DetFuzz\volume\windows-security-logon-sample.xml |
  Select-Object FullName, Length
```

Use that data to update:

```text
measurements/source_volumes_lab_sample.yaml
```

Keep the status honest. Use `lab_24h_measurement` only after a real 24-hour
window is measured.
