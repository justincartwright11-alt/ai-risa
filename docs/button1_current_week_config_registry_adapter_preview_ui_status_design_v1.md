# Button 1 Current-Week Config Registry Adapter Preview UI Status Design v1

## Slice
button1-current-week-config-registry-adapter-preview-ui-status-design-v1

## Baseline
- Slice: button1-current-week-config-registry-adapter-runtime-preview-scaffold-v1
- Commit: 531882d
- Tag: button1-current-week-config-registry-adapter-runtime-preview-scaffold-v1

## Goal
Define how Button 1 UI should present `registry_adapter_status` in the preview/runtime surface before any UI code changes are made.

## Scope
- In scope: UI information architecture, status display contract, fail-closed messaging, operator-governance messaging, and non-interactive preview behavior.
- Out of scope: UI implementation code, runtime wiring changes, provider execution, source calls, scraping, queue/database writes, auto-save, Button 2 changes, and Button 3 changes.

## Current Runtime Contract (Already Available)
Button 1 preview/runtime payload now includes:
- `registry_adapter_status`

Expected fields currently available:
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

## UI Display Intent
The Button 1 UI should expose registry-adapter status as a read-only governance panel that answers:
1. Is adapter input valid?
2. How many registry candidates are available?
3. How many candidates are enabled?
4. Why is status blocked when fail-closed?
5. Are execution/network/write paths still disabled?

## Proposed Panel Placement
Place a new read-only panel in Button 1 Find Fights status area, near existing runtime status lines.

Suggested section title:
- Registry Adapter Status (Preview)

Suggested order within panel:
1. Adapter Validity
2. Candidate Count
3. Enabled Candidate Count
4. Candidate IDs (collapsed by default)
5. Diagnostics
6. Governance Flags

## Proposed UI Fields and Labels
- Adapter Validity: `registry_candidate_valid`
- Registration Valid: `registration_valid`
- Validation Valid: `validation_valid`
- Candidate Count: `registry_candidate_count`
- Enabled Candidate Count: length of `enabled_registry_candidate_ids`
- Schema Version: `registry_candidate_schema_version`
- Diagnostics: `diagnostics`
- Operator Approval Required: `operator_approval_required`
- Provider Execution Performed: `provider_execution_performed`
- Network Calls Performed: `network_calls_performed`
- Queue Write Performed: `queue_write_performed`
- Database Write Performed: `database_write_performed`

## Status Semantics for UI
### Green (informational only)
Use green badge only when all are true:
- `registry_candidate_valid=true`
- `registration_valid=true`
- `validation_valid=true`

Even when green:
- Must still display `operator_approval_required=true`
- Must still display no-execution/no-network/no-write flags

### Amber (attention)
Use amber when:
- Candidate bundle exists but not ready for activation contexts
- Diagnostics present but non-fatal

### Red (fail-closed)
Use red when any fail-closed blocker appears, including:
- `registry_candidate_valid=false`
- `registration_valid=false`
- `validation_valid=false`
- duplicate provider ID diagnostics
- missing/invalid config diagnostics

## Fail-Closed Message Templates
When blocked, display concise operator-readable messages:
- Missing config: "Registry adapter unavailable: provider config missing."
- Invalid config: "Registry adapter blocked: provider config invalid."
- Duplicate provider ID: "Registry adapter blocked: duplicate provider_id detected."
- Approval missing: "Registry adapter blocked: enabled provider missing operator approval."

## Candidate List Presentation
Candidate list should be collapsed by default.

For each candidate row, show:
- `provider_id`
- `provider_name`
- `enabled`
- `candidate_status`

Do not show:
- raw internal objects
- execution interfaces
- provider adapter internals

## Governance Banner
Include a fixed mini-banner under the panel:
- "Preview only. No provider execution, no live source calls, and no queue/database writes are performed in this status view."

## UX Non-Interactive Rules
- No action buttons in this panel.
- No "Activate" or "Run Provider" affordances.
- No write/apply controls.
- No Button 2 promotion controls.

## Accessibility and Clarity
- Use explicit text labels, not color-only meaning.
- Surface diagnostics as plain text list.
- Provide default fallback text when fields are absent.

## Integration Contract (Future UI Slice)
A future UI implementation slice should only read from existing payload path:
- `workflow.jobs[0].input_ref.metadata.payload.registry_adapter_status`

The UI slice must not:
- call provider code
- call source URLs
- mutate queue/database state

## Future UI Test Expectations
- Panel renders when `registry_adapter_status` exists
- Panel renders fail-closed state when invalid
- Diagnostics list appears with deterministic ordering
- Governance flags are visible and remain false for execution/network/write
- No new UI controls introduce write actions
- Button 2 unchanged
- Button 3 unchanged

## Governance
- Design-only slice.
- No code changes to UI runtime implementation.
- No provider execution introduced.
- No network/scraping introduced.
- No queue/database writes introduced.
- No Button 2 or Button 3 changes.

## Non-Goals
- No visual redesign of unrelated panels
- No dashboard layout refactor
- No backend contract changes
- No state mutation controls
