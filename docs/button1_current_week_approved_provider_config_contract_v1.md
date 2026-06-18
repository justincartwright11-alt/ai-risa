# Button 1 Current-Week Approved Provider Config Contract v1

## Slice
button1-current-week-approved-provider-config-contract-v1

## Baseline
- Slice: button1-current-week-live-source-provider-runtime-integration-preview-v1
- Commit: fae8d29
- Tag: button1-current-week-live-source-provider-runtime-integration-preview-v1

## Goal
Define the approved-provider configuration contract for Button 1 current-week/upcoming discovery before any real provider is plugged in.

## Scope
- In scope: config shape, validation rules, governance requirements, fail-closed semantics, and future implementation test expectations.
- Out of scope: provider implementation, scraping, web API calls, runtime wiring, Button 2 changes, Button 3 changes, queue/database writes, or customer report generation.

## Approved Provider Registry Shape
The registry is a config-only collection of approved provider entries. It may be represented as JSON, YAML, or equivalent structured config, but each entry must normalize to the same required fields.

### Required provider fields
Each provider entry must define:
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

### Registry-level expectations
- Registry must be explicit, deterministic, and operator-approved.
- Provider entries must be rejectable independently.
- Unknown providers must not be auto-accepted.
- Missing registry config must fail closed.

## Disallowed Provider States
Any of the following states must be rejected as invalid config:
- missing approval
- missing allowed domain
- unknown source tier
- expired approval
- stale feed age rule missing
- unsupported schema version
- provider enabled without operator approval

## Fail-Closed Config Behavior
The Button 1 discovery path must interpret config outcomes as follows:
- no config = unavailable
- invalid config = unavailable
- disabled provider = unavailable
- provider enabled but not approved = unavailable
- provider approved but stale = stale
- provider valid but no events in window = no_current_week_source_backed_matchups

## Governance
The config contract must preserve these rules:
- no random scraping
- no unapproved providers
- no permanent queue/database save without operator approval
- no customer report generation from provider output alone
- source provenance required
- diagnostics required
- rollback/audit required before implementation

## Future Implementation Tests
The next implementation slice should validate:
- valid config loads
- invalid config blocks
- enabled but unapproved blocks
- unsupported schema blocks
- stale config/feed blocks
- valid config still does not bypass operator approval
- Button 2 unchanged
- Button 3 unchanged

## Notes for the Next Slice
The next safe implementation should be a config parser/validator scaffold only. It must not contact live sources or change preview/runtime behavior beyond config validation.
