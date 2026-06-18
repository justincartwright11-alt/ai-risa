# Button 1 Current-Week Config Registry Adapter Runtime Preview Scaffold v1

## Slice
button1-current-week-config-registry-adapter-runtime-preview-scaffold-v1

## Baseline
- Slice: button1-current-week-config-registry-adapter-runtime-preview-design-v1
- Commit: 5929daa
- Tag: button1-current-week-config-registry-adapter-runtime-preview-design-v1

## Goal
Expose registry-adapter status inside Button 1 preview/runtime payloads as read-only metadata while keeping provider execution and live-source calls disabled.

## Scope
- In scope: runtime preview payload surface for adapter status, fail-closed missing-config behavior, governance flags, and integration tests.
- Out of scope: provider execution, source collection, scraping, queue/database writes, auto-save, Button 2 changes, and Button 3 changes.

## Implementation Summary
- Added a read-only runtime helper that loads registration output and adapter candidates from local config paths only.
- Added `registry_adapter_status` to Button 1 runtime preview payload.
- Preserved fail-closed behavior when registry config is missing.
- Preserved governance flags as false for execution/write paths.

## Runtime Preview Contract Additions
`workflow.jobs[0].input_ref.metadata.payload` now includes:
- `registry_adapter_status`

Expected key fields inside `registry_adapter_status`:
- `registry_candidate_valid`
- `registration_valid`
- `validation_valid`
- `registry_candidate_schema_version`
- `registry_candidate_count`
- `registry_candidates`
- `enabled_registry_candidate_ids`
- `diagnostics`
- `network_calls_performed`
- `provider_execution_performed`
- `queue_write_performed`
- `database_write_performed`
- `operator_approval_required`

## Required Behavior
- Missing registry config must fail closed.
- Preview payload must still include adapter-status diagnostics.
- Provider execution remains false.
- Network calls remain false.
- Queue/database writes remain false.
- Button 2 and Button 3 remain unchanged.

## Governance
- No provider execution introduced.
- No live source calls introduced.
- No scraping introduced.
- No queue/database writes introduced.
- No auto-save or Button 2 promotion introduced.
- Approval remains required.

## Validation
- Runtime workflow preview includes `registry_adapter_status`.
- Missing config returns fail-closed adapter status.
- Governance flags remain false.
- Existing Button 1 parser/registration/orchestrator/runtime tests remain green.

## Non-Goals
- No change to orchestrator execution behavior.
- No provider activation.
- No source fetch implementation.
