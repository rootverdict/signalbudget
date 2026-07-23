# SignalBudget Pareto Analysis

Configuration count: `8`
Complete-cost configurations: `8`
Partial-cost configurations: `0`

Pricing status: `PRICING_FRESH`

## Non-Dominated Complete-Cost Configurations

- `none`: status `NON_DOMINATED`, proxy cost `0.0`, validated detections `0`, investigation questions `0`
- `powershell_script_block`: status `NON_DOMINATED`, proxy cost `0.0031863`, validated detections `0`, investigation questions `1`
- `powershell_script_block+windows_security_logon`: status `NON_DOMINATED`, proxy cost `0.05226951`, validated detections `0`, investigation questions `2`
- `sysmon_process_create`: status `NON_DOMINATED`, proxy cost `0.2499246`, validated detections `1`, investigation questions `2`
- `sysmon_process_create+powershell_script_block`: status `NON_DOMINATED`, proxy cost `0.2531109`, validated detections `1`, investigation questions `3`
- `sysmon_process_create+windows_security_logon`: status `NON_DOMINATED`, proxy cost `0.29900781`, validated detections `1`, investigation questions `4`
- `sysmon_process_create+powershell_script_block+windows_security_logon`: status `NON_DOMINATED`, proxy cost `0.30219411`, validated detections `1`, investigation questions `5`

## Dominated Complete-Cost Configurations

- `windows_security_logon`: status `DOMINATED`, proxy cost `0.04908321`, validated detections `0`, investigation questions `1`

## Boundary

All configurations have complete lab-derived cost estimates. Pareto status is final within the current three-source lab measurement set.
