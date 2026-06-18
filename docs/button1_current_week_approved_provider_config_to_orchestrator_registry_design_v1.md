# Button 1 Current-Week Approved Provider Config to Orchestrator Registry Design v1

## Slice
button1-current-week-approved-provider-config-to-orchestrator-registry-design-v1

## Baseline
- Slice: button1-current-week-approved-provider-config-registration-scaffold-v1
- Commit: fdae3ca
- Tag: button1-current-week-approved-provider-config-registration-scaffold-v1

## Goal
Define how Button 1 approved-provider registration output will connect to the orchestrator registry shape before any runtime wiring, provider execution, or live source access occurs.

## Scope
- In scope: data handoff shape, registry normalization rules, source-of-truth boundaries, contract field mapping, and fail-closed behavior between registration and orchestration.
- Out of scope: provider execution, network calls, scraping, runtime loader changes, live source wiring, queue/database writes, auto-save, Button 2 changes, and Button 3 changes.

## Design Intent
The registration slice already proves that validated config can be converted into a registry-shaped object without execution. This design slice defines the next boundary:
- registration output is treated as a registry candidate
- orchestrator consumes the registry candidate as read-only input
- no provider is instantiated unless a later runtime slice explicitly authorizes it
- invalid or duplicate registry material remains fail-closed

## Handoff Contract
The registration output must be mappable into an orchestrator registry record set without loss of governance state.

### Registration output fields considered authoritative
- `registration_valid`
- `validation_valid`
- `feed_status`
- `current_week_ready`
- `save_allowed`
- `diagnostics`
- `config_path`
- `provider_count`
- `registered_provider_count`
- `enabled_provider_count`
- `registered_provider_ids`
- `enabled_provider_ids`
- `registry_schema_version`
- `network_calls_performed`
- `provider_execution_performed`
- `queue_write_performed`
- `database_write_performed`
- `operator_approval_required`

### Registry-side fields that may be derived from registration output
- registry schema version
- registry entry count
- enabled entry count
- provider identity list
- enabled identity list
- diagnostics summary
- operator approval status

## Registry Normalization Rules
1. Registry input must be treated as read-only structured config.
2. `registered_provider_ids` and `enabled_provider_ids` must remain deterministic and ordered as emitted by registration.
3. Duplicate provider identifiers remain invalid at the registry boundary.
4. `operator_approval_required` must remain true until a separate governance slice changes it.
5. `network_calls_performed`, `provider_execution_performed`, `queue_write_performed`, and `database_write_performed` must remain false in this design boundary.
6. If registration output is invalid, the orchestrator registry must not be promoted to active discovery use.

## Orchestrator Registry Shape
The orchestrator registry is the next internal shape that will be consumed by a later runtime slice. It should represent a normalized list of provider descriptors with metadata only.

### Conceptual registry entry fields
- `provider_id`
- `provider_name`
- `provider_type`
- `enabled`
- `source_tier`
- `allowed_domains`
- `endpoint_or_feed_location`
- `auth_required`
- `refresh_cadence_minutes`
- `max_feed_age_hours`
- `ruleset_scope`
- `promotion_scope`
- `region_scope`
- `output_schema_version`
- `operator_approved_by`
- `approval_timestamp_utc`
- `provenance_notes`

### Registry-level metadata
- `registry_schema_version`
- `provider_count`
- `enabled_provider_count`
- `registration_valid`
- `validation_valid`
- `diagnostics`
- `operator_approval_required`

## State Mapping

### valid registration -> valid registry candidate
If registration is valid:
- the registry candidate may be built from the normalized provider list
- enabled provider metadata may be exposed as a preview artifact
- no execution is permitted
- no active discovery state is implied

### invalid registration -> blocked registry candidate
If registration is invalid:
- the orchestrator registry must remain unavailable for active use
- diagnostics must be preserved
- no provider activation may occur

### duplicate provider identifiers -> blocked registry candidate
If duplicate provider identifiers are present:
- the registry candidate must fail closed
- duplicate diagnostics must remain visible
- no deduped active registry should be silently substituted

### enabled-but-unapproved state -> blocked registry candidate
If a provider is marked enabled without required operator approval:
- the registry candidate must fail closed
- the enabled status must not be elevated into live readiness

## Governance Boundaries
This design preserves the current safety model:
- no random scraping
- no live source calls
- no provider adapter execution
- no queue promotion
- no database write
- no customer report generation
- no Button 2 or Button 3 behavior change

## Future Integration Shape
A later runtime slice may introduce a helper that:
- accepts registration output
- normalizes it into an orchestrator registry object
- forwards only read-only metadata into preview payloads
- refuses to activate anything when validation or governance checks fail

That future slice must still remain fail-closed and approval-gated.

## Required Test Expectations for the Next Implementation Slice
The next implementation slice should validate:
- registration output maps cleanly into registry metadata
- invalid registration blocks registry activation
- duplicate provider IDs remain blocked
- enabled provider metadata is preserved without execution
- operator approval remains required
- no network calls are introduced
- no provider execution is introduced
- no queue/database writes are introduced
- Button 2 unchanged
- Button 3 unchanged

## Non-Goals
- No runtime helper implementation
- No provider adapter execution
- No live source refresh wiring
- No queue save logic
- No database persistence
- No changes to Button 2 or Button 3

## Notes for the Next Slice
The next safe implementation slice should focus on a thin orchestrator-registry adapter that consumes registration output only as structured input. It should not call live providers or alter the current fail-closed runtime behavior.
