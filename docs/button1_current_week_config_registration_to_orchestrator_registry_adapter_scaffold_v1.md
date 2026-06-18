# Button 1 Current-Week Config Registration to Orchestrator Registry Adapter Scaffold v1

## Slice
button1-current-week-config-registration-to-orchestrator-registry-adapter-scaffold-v1

## Baseline
- Slice: button1-current-week-approved-provider-config-to-orchestrator-registry-design-v1
- Commit: 9af0911
- Tag: button1-current-week-approved-provider-config-to-orchestrator-registry-design-v1

## Goal
Build a pure adapter scaffold that converts Button 1 approved-provider registration output into orchestrator registry candidates without executing providers or contacting live sources.

## Scope
- In scope: registration-output normalization, registry-candidate mapping, fail-closed behavior, and governance-preserving metadata pass-through.
- Out of scope: provider execution, live source calls, scraping, runtime loader changes, queue/database writes, auto-save, Button 2 changes, and Button 3 changes.

## Input Contract
The adapter consumes registration output only. It must treat the registration result as read-only metadata and must not re-read config files or re-run validation.

Required input fields to consume:
- `registration_valid`
- `validation_valid`
- `feed_status`
- `current_week_ready`
- `save_allowed`
- `diagnostics`
- `config_path`
- `registration_schema_version`
- `provider_count`
- `registered_provider_count`
- `enabled_provider_count`
- `registered_provider_ids`
- `registered_provider_names`
- `enabled_provider_ids`
- `network_calls_performed`
- `provider_execution_performed`
- `queue_write_performed`
- `database_write_performed`
- `operator_approval_required`

## Registry Candidate Shape
The adapter produces a registry-candidate bundle with:
- `registry_candidate_valid`
- `registry_candidate_schema_version`
- `registry_candidate_count`
- `registry_candidates`
- `enabled_registry_candidate_ids`
- registration metadata passthrough
- preserved governance flags

### Conceptual candidate entry fields
- `provider_id`
- `provider_name`
- `enabled`
- `candidate_status`
- `source_of_truth`
- `registry_candidate_valid`
- `network_calls_performed`
- `provider_execution_performed`
- `queue_write_performed`
- `database_write_performed`
- `operator_approval_required`

## Mapping Rules
1. Valid registration maps to one registry candidate per registered provider.
2. Disabled providers remain represented as disabled registry candidates.
3. Enabled providers remain represented as enabled registry candidates.
4. Invalid registration fails closed and produces no active registry candidates.
5. Duplicate provider IDs remain blocked and must not be silently deduped.
6. Diagnostics are preserved unchanged.
7. Governance flags remain false for execution/write activity.
8. Operator approval remains required.

## Governance
- No provider execution.
- No live source access.
- No web scraping.
- No queue/database writes.
- No auto-save.
- No Button 2 or Button 3 changes.

## Future Tests
- valid registration maps to registry candidates
- disabled registration maps to disabled candidate
- invalid registration fails closed with no candidates
- validation-invalid registration fails closed
- duplicate provider ID remains blocked
- non-dict input fails closed
- no network calls are introduced
- no provider execution is introduced
- queue/database writes remain false
- operator approval required remains true
- Button 2 unchanged
- Button 3 unchanged

## Non-Goals
- No runtime wiring to the live orchestrator service
- No provider adapter invocation
- No source discovery or refresh behavior
- No persistence layer behavior

## Notes for the Next Slice
The next safe implementation slice can wire this adapter into an orchestrator-registry preview path, but only as a read-only transformation of registration output. It must still not execute providers or call sources.
