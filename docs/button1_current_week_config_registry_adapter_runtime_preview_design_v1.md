# Button 1 Current-Week Config Registry Adapter Runtime Preview Design v1

## Slice
button1-current-week-config-registry-adapter-runtime-preview-design-v1

## Baseline
- Slice: button1-current-week-config-registration-to-orchestrator-registry-adapter-scaffold-v1
- Commit: 0666aca
- Tag: button1-current-week-config-registration-to-orchestrator-registry-adapter-scaffold-v1

## Goal
Define how Button 1 preview/runtime will consume orchestrator registry candidates produced by the registration-to-registry adapter, without wiring execution, source calls, or live provider activation yet.

## Scope
- In scope: preview/runtime consumption shape, candidate selection rules, fail-closed status mapping, metadata pass-through, and governance boundaries.
- Out of scope: provider execution, live source calls, scraping, queue/database writes, auto-save, Button 2 changes, and Button 3 changes.

## Design Intent
The adapter slice already converts registration output into registry candidates. This slice defines how a later runtime preview layer will read those candidates and present status without activating any provider.

The runtime preview layer must treat registry candidates as read-only metadata and must not:
- instantiate providers
- call collect methods
- refresh sources
- write queue rows
- write database rows
- promote fights

## Candidate Consumption Model
The runtime preview layer should consume the adapter result as a structured preview bundle containing:
- registry candidate validity
- registry candidate count
- candidate identifiers
- enabled candidate identifiers
- preserved diagnostics
- governance flags
- schema version markers

### Primary inputs
- `registry_candidate_valid`
- `registry_candidate_schema_version`
- `registry_candidate_count`
- `registry_candidates`
- `enabled_registry_candidate_ids`
- `registration_valid`
- `validation_valid`
- `diagnostics`
- `operator_approval_required`
- `network_calls_performed`
- `provider_execution_performed`
- `queue_write_performed`
- `database_write_performed`

### Runtime preview outputs
A later preview helper may emit:
- `feed_status`
- `current_week_ready`
- `save_allowed`
- `feed_used`
- `fallback_used`
- `source_freshness`
- `feed_age_seconds`
- `current_week_rows_count`
- `approved_source_event_rows_count`
- `source_backed_event_cards`
- `diagnostics`

## Design Rules
1. Registry candidates are preview-only until a separate execution slice explicitly authorizes activation.
2. Candidate validity must remain fail-closed when registration is invalid.
3. Candidate metadata must not be mutated into readiness without a future runtime source proof.
4. Enabled candidates may be shown, but not executed, in preview.
5. Diagnostics from registration and adapter layers must remain visible to runtime preview consumers.
6. Approval requirements must remain true until a separate governance slice changes them.

## Fail-Closed Preview States
The runtime preview layer should map candidate states as follows:
- invalid candidate bundle = unavailable
- empty candidate bundle = unavailable
- enabled candidate without runtime proof = unavailable
- candidate bundle with no in-window source proof = no_current_week_source_backed_matchups
- future fresh source proof only = current_week_ready

## Governance
- No execution path is introduced.
- No live provider adapter is invoked.
- No source fetch is performed.
- No queue/database write is performed.
- No auto-save or auto-promotion is performed.
- Button 2 and Button 3 remain unchanged.

## Future Tests
The next implementation slice should validate:
- valid registry candidates are readable by preview/runtime
- invalid registry candidates stay unavailable
- empty candidate bundles stay unavailable
- diagnostics survive the handoff
- approval remains required
- no execution is introduced
- no network calls are introduced
- no queue/database writes are introduced
- Button 2 unchanged
- Button 3 unchanged

## Non-Goals
- No runtime wiring implementation
- No live source collection
- No provider execution
- No persistence behavior
- No queue promotion

## Notes for the Next Slice
The next safe implementation slice may add a thin preview helper that accepts adapter candidates and returns read-only runtime status. It must still remain fail-closed and must not activate any provider or source.
