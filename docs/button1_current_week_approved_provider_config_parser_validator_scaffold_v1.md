# Button 1 Current-Week Approved Provider Config Parser / Validator Scaffold v1

## Slice
button1-current-week-approved-provider-config-parser-validator-scaffold-v1

## Baseline
- Slice: button1-current-week-approved-provider-config-contract-v1
- Commit: 920bb12
- Tag: button1-current-week-approved-provider-config-contract-v1

## Goal
Build a Button 1 approved-provider config parser/validator scaffold that validates config only and fails closed on missing or invalid configuration.

## Scope
- In scope: config parsing, registry validation, contract enforcement, deterministic fail-closed output, and validation diagnostics.
- Out of scope: real provider implementation, scraping, web API calls, live source discovery wiring, queue/database writes, Button 2, and Button 3.

## Required Behavior
- Missing config path => unavailable, no ready state, no save allowed, diagnostics include `provider_config_missing`.
- Invalid JSON => unavailable, diagnostics include `provider_config_invalid_json`.
- Missing required fields => unavailable, diagnostics include `missing_required_field:<field>`.
- enabled=true without operator approval => unavailable, diagnostics include `provider_enabled_without_operator_approval`.
- Missing allowed domains => unavailable, diagnostics include `missing_allowed_domains`.
- Unknown source tier => unavailable, diagnostics include `unknown_source_tier`.
- Unsupported schema version => unavailable, diagnostics include `unsupported_output_schema_version`.
- Missing max_feed_age_hours => unavailable, diagnostics include `missing_max_feed_age_hours`.
- Valid disabled config => valid, enabled_provider_count = 0, diagnostics include `no_enabled_provider`.
- Valid enabled approved config => valid, enabled_provider_count >= 1, with no network or provider execution.

## Output Contract
The validator result must include:
- valid
- feed_status
- current_week_ready
- save_allowed
- diagnostics
- provider_count
- enabled_provider_count
- enabled_provider_ids
- config_path
- schema_version
- network_calls_performed
- provider_execution_performed
- queue_write_performed
- database_write_performed

## Governance
- No random scraping.
- No unapproved providers.
- No permanent queue/database save without operator approval.
- No customer report generation from config validation alone.
- Source provenance required.
- Diagnostics required.
- Rollback/audit required before any future implementation.

## Future Implementation Tests
- missing config fails closed
- invalid JSON fails closed
- missing required field fails closed
- enabled without approval fails closed
- missing allowed domains fails closed
- unknown source tier fails closed
- unsupported schema version fails closed
- valid disabled config passes validation but enables zero providers
- valid enabled approved config passes validation but performs no network/provider execution
- Button 2 unchanged
- Button 3 unchanged
