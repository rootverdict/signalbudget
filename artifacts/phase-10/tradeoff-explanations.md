# SignalBudget Tradeoff Explanations

Pricing status: `PRICING_FRESH`

## Evidence Caveat

Cost estimates are lab-derived from 24-hour VM measurements and are not production forecasts.

## Source Removal Losses

### Remove `powershell_script_block`

Lost detections:
- `powershell_script_block_encoded_activity`

Lost investigation questions:
- `powershell_script_content`

### Remove `sysmon_process_create`

Lost detections:
- `d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62`

Lost investigation questions:
- `process_command_line`
- `parent_child_process`
- `user_to_process_context`

### Remove `windows_security_logon`

Lost detections:
- `windows_failed_logon_context`

Lost investigation questions:
- `logon_success_failure`
- `user_to_process_context`

## Frontier Tradeoffs

- Baseline: `none` costs $0.00000000/month as `XML_EXPORT_SIZE_PROXY`, with 0 validated detections and 0 investigation questions.
- Moving from `none` to `powershell_script_block` changes cost by $0.00318630/month as `XML_EXPORT_SIZE_PROXY`, adds detections `powershell_script_block_encoded_activity`, loses detections none, adds questions `powershell_script_content`, and loses questions none.
- Moving from `powershell_script_block` to `powershell_script_block+windows_security_logon` changes cost by $0.04908321/month as `XML_EXPORT_SIZE_PROXY`, adds detections `windows_failed_logon_context`, loses detections none, adds questions `logon_success_failure`, and loses questions none.
- Moving from `powershell_script_block+windows_security_logon` to `sysmon_process_create` changes cost by $0.19765509/month as `XML_EXPORT_SIZE_PROXY`, adds detections `d4f8c4e4-984d-4f5f-9f6c-1cc6b37f2f62`, loses detections `powershell_script_block_encoded_activity`, `windows_failed_logon_context`, adds questions `parent_child_process`, `process_command_line`, and loses questions `logon_success_failure`, `powershell_script_content`.
- Moving from `sysmon_process_create` to `sysmon_process_create+powershell_script_block` changes cost by $0.00318630/month as `XML_EXPORT_SIZE_PROXY`, adds detections `powershell_script_block_encoded_activity`, loses detections none, adds questions `powershell_script_content`, and loses questions none.
- Moving from `sysmon_process_create+powershell_script_block` to `sysmon_process_create+windows_security_logon` changes cost by $0.04589691/month as `XML_EXPORT_SIZE_PROXY`, adds detections `windows_failed_logon_context`, loses detections `powershell_script_block_encoded_activity`, adds questions `logon_success_failure`, `user_to_process_context`, and loses questions `powershell_script_content`.
- Moving from `sysmon_process_create+windows_security_logon` to `sysmon_process_create+powershell_script_block+windows_security_logon` changes cost by $0.00318630/month as `XML_EXPORT_SIZE_PROXY`, adds detections `powershell_script_block_encoded_activity`, loses detections none, adds questions `powershell_script_content`, and loses questions none.
