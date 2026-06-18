# Button 1 Approved Provider Real Registry Design v1

Slice: button1-current-week-approved-provider-real-registry-design-v1
Date: 2026-06-18
Status: Design-only (no runtime file creation, no provider execution)

## Purpose

Define the requirements for the real runtime registry file before creating:

- ops/approved_sources/button1_live_provider_registry.json

This document is a contract-first design artifact only. It does not enable execution, discovery, network calls, queue writes, or database writes.

## Scope

In scope:
- Runtime registry data contract definition
- Validation requirements and fail-closed behavior
- Governance controls and operator approval requirements
- Acceptance criteria for a future implementation slice

Out of scope:
- Creating ops/approved_sources/button1_live_provider_registry.json
- Running providers or network fetches
- Auto-discovery implementation
- Queue persistence implementation
- Button 2 or Button 3 behavior changes

## Current Baseline

Current runtime target remains:
- ops/approved_sources/button1_live_provider_registry.json

Current runtime behavior remains fail-closed when file is absent:
- diagnostics includes provider_config_missing
- provider_execution_performed=false
- network_calls_performed=false
- queue_write_performed=false
- database_write_performed=false

The disabled example file remains non-runtime:
- ops/approved_sources/button1_live_provider_registry.example.disabled.v1.json

## Runtime Registry Contract (Proposed)

Top-level JSON object:
- schema_version: string, required, must equal button1_live_provider_registry_v1
- providers: array of provider objects, required

Provider object required fields (must all exist):
- provider_id
- provider_name
- provider_type
- enabled
- source_tier
- allowed_domains
- endpoint_or_feed_location
- auth_required
- refresh_cadence_minutes
- max_feed_age_hours
- ruleset_scope
- promotion_scope
- region_scope
- output_schema_version
- operator_approved_by
- approval_timestamp_utc
- provenance_notes

Field constraints:
- output_schema_version must equal button1_live_provider_registry_v1
- source_tier must be one of:
  - official_promotion
  - official_commission
  - verified_database
  - internal_operator_approved
- allowed_domains must be a non-empty array of non-empty strings
- endpoint_or_feed_location must be non-empty string
- enabled must be boolean
- auth_required must be boolean
- refresh_cadence_minutes should be positive integer
- max_feed_age_hours should be positive integer
- ruleset_scope should be non-empty array
- promotion_scope should be non-empty array
- region_scope should be non-empty array
- approval_timestamp_utc must be parseable ISO UTC timestamp

Operator approval constraints:
- If enabled=true:
  - operator_approved_by must be non-empty
  - approval_timestamp_utc must be valid
- If enabled=false:
  - provider remains non-executable by policy

## Governance Requirements

Mandatory governance behavior until explicit execution slice is approved:
- No provider execution from registry presence alone
- No source calls from registry presence alone
- No queue/database writes from registry presence alone
- No customer report generation trigger from registry presence alone
- Operator approval remains required for any future execution path

Telemetry flags must remain false in preview/runtime status payloads during design-only stage:
- provider_execution_performed=false
- network_calls_performed=false
- queue_write_performed=false
- database_write_performed=false

## Fail-Closed Rules

Fail-closed conditions and required outcomes:

1. File missing
- Diagnostic: provider_config_missing
- valid=false
- enabled_provider_count=0
- feed_status=unavailable

2. Invalid JSON or wrong shape
- Diagnostic: provider_config_invalid_json
- valid=false

3. Unknown or unsupported schema
- Diagnostic: unsupported_output_schema_version
- valid=false

4. Missing required provider fields
- Diagnostic: missing_required_field:<field>
- valid=false

5. Missing domains or source limits
- Diagnostic: missing_allowed_domains and/or missing_max_feed_age_hours
- valid=false

6. Unknown source tier
- Diagnostic: unknown_source_tier
- valid=false

7. No enabled providers in an otherwise valid file
- Diagnostic: no_enabled_provider
- valid=true (contract valid), execution still not enabled in this stage

## Example Valid Shape (Design Reference Only)

This is a design reference snippet only, not a runtime activation instruction.

{
  "schema_version": "button1_live_provider_registry_v1",
  "providers": [
    {
      "provider_id": "ufc_official_events",
      "provider_name": "UFC Official Events",
      "provider_type": "official",
      "enabled": false,
      "source_tier": "official_promotion",
      "allowed_domains": ["ufc.com"],
      "endpoint_or_feed_location": "https://www.ufc.com/events",
      "auth_required": false,
      "refresh_cadence_minutes": 120,
      "max_feed_age_hours": 24,
      "ruleset_scope": ["event_card_discovery"],
      "promotion_scope": ["UFC"],
      "region_scope": ["global"],
      "output_schema_version": "button1_live_provider_registry_v1",
      "operator_approved_by": "operator@example.com",
      "approval_timestamp_utc": "2026-06-18T00:00:00Z",
      "provenance_notes": "Design reference provider entry"
    }
  ]
}

## Implementation Boundary for Next Runtime Slice

Preconditions before creating ops/approved_sources/button1_live_provider_registry.json:
- Design doc accepted and locked
- Operator approval policy signed off
- Validation tests for contract and fail-closed behavior ready
- Explicit non-execution guarantee preserved until separate execution slice

When real runtime registry file is first introduced, that slice must:
- Be isolated to config introduction and validation proof only
- Prove no automatic provider execution occurs
- Prove no network calls/writes are triggered by file existence
- Keep Button 2 and Button 3 unaffected

## Acceptance Criteria (Design Slice)

This design slice is complete when:
- Real registry requirements are documented end-to-end
- Governance constraints are explicit and testable
- Fail-closed behavior is specified for all key failure modes
- Next implementation boundary is clearly defined
- No runtime/UI behavior changes are introduced

## Non-Regression Commitments

This design-only slice must preserve:
- Runtime code changed: false
- UI code changed: false
- Provider execution: not implemented
- Auto-discovery: not implemented
- Queue persistence: not implemented
- Customer report generation trigger: not implemented
- Button 2 unaffected
- Button 3 unaffected

## Conclusion

The real runtime registry design is now defined and constrained by fail-closed governance.
The actual runtime file creation is intentionally deferred to a future implementation slice with explicit operator-approval boundaries and non-execution proof requirements.
