# Button 1 Current-Week Approved Provider Config Registration Scaffold v1

## Slice
button1-current-week-approved-provider-config-registration-scaffold-v1

## Baseline
- Slice: button1-current-week-approved-provider-config-parser-validator-scaffold-v1
- Commit: 05e866d
- Tag: button1-current-week-approved-provider-config-parser-validator-scaffold-v1

## Goal
Build a config-only registration scaffold that converts validated Button 1 approved-provider config into an orchestrator registry shape without enabling real providers.

## Scope
- In scope: registration mapping, duplicate ID checks, approved-state enforcement, registry-shaped output, and fail-closed diagnostics.
- Out of scope: provider execution, live source calls, scraping, auto-save, Button 2 changes, and Button 3 changes.

## Required Behavior
- Missing config => registration_valid false, feed_status unavailable, zero registered providers.
- Invalid config => registration_valid false, feed_status unavailable, zero registered providers.
- Valid disabled config => registration_valid true, zero enabled providers, diagnostics include no_enabled_provider.
- Valid enabled approved config => registration_valid true, enabled metadata exposed, but no network/provider execution.
- Duplicate provider_id => registration_valid false, diagnostics include duplicate_provider_id:.
- Enabled provider with invalid approval => registration_valid false, diagnostics include provider_enabled_without_operator_approval.

## Output Contract
The registration result must include:
- registration_valid
- validation_valid
- feed_status
- current_week_ready
- save_allowed
- diagnostics
- config_path
- provider_count
- registered_provider_count
- enabled_provider_count
- registered_provider_ids
- enabled_provider_ids
- registry_schema_version
- network_calls_performed
- provider_execution_performed
- queue_write_performed
- database_write_performed
- operator_approval_required

## Governance
- No real provider is created or enabled.
- No provider adapters are executed.
- No web sources are contacted.
- No scraping is performed.
- No fights are auto-saved or auto-promoted.
- Button 2 and Button 3 remain unchanged.

## Future Tests
- missing config fails closed and registers zero providers
- invalid config fails closed and registers zero providers
- valid disabled config registers but enables zero providers
- valid enabled approved config registers enabled provider metadata
- duplicate provider_id fails closed
- enabled but unapproved provider fails closed
- registration performs no network calls
- registration performs no provider execution
- queue/database writes remain false
- operator approval required remains true
- Button 2 unchanged
- Button 3 unchanged
