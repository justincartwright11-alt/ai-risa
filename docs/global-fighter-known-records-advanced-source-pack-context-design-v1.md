# global-fighter-known-records-advanced-source-pack-context-design-v1

## Purpose
Design the advanced known-record source pack context before implementation. This document defines how approved historical fighter records, report-history projections, result-ledger projections, and future global database read-only projections should safely feed known_records into the identity resolver preview.

## Scope
- **Docs-only**: No code, no API, no UI changes in this slice.
- **Governance**: Advanced source packs may improve identity matching, but may not create, update, merge, rank, or write fighter profiles.
- **Preview-only**: All new context is strictly read-only and preview-only.

## Context Sources
1. **Approved Historical Fighter Records**
   - Read-only, operator-approved records from prior events.
   - No mutation, no learning, no writeback.
2. **Report-History Projections**
   - Aggregated, sanitized data from previously generated premium reports.
   - Used for context, not for profile mutation.
3. **Result-Ledger Projections**
   - Read-only projections from official result ledgers.
   - No direct profile update or learning.
4. **Future Global Database Read-Only Projections**
   - Planned: read-only, operator-approved global fighter database context.
   - No write, merge, or ranking allowed.

## Safety Invariants
- No profile create/update/merge/rank/write.
- No learning/calibration writes.
- No filesystem writes.
- No live web calls.
- All new context is preview-only and summary-only.
- Normal dashboard remains 3 buttons / 3 gates.

## Design Principles
- **Deterministic Precedence**: Advanced source packs must define clear, deterministic precedence rules for context sources (e.g., official records > report-history > result-ledger > global DB).
- **Dedupe & Sanitization**: All context must be deduped and sanitized before feeding into the identity resolver preview.
- **Operator Approval**: Only operator-approved data may be surfaced in advanced source packs.
- **Zero-Mutation Guarantee**: No code path may mutate, merge, or write to any fighter profile or global database.

## Example Context Flow
1. User triggers Button 1 identity resolver preview.
2. Advanced source pack builder aggregates context from all approved sources.
3. Context is deduped, sanitized, and precedence-applied.
4. Preview-only summary is passed to the identity resolver preview.
5. No write, merge, or learning occurs at any step.

## Out-of-Scope
- No new API endpoints, UI controls, or backend write paths.
- No changes to operator approval gates.
- No changes to 3-button/3-gate dashboard structure.

## Next Steps
- Review and lock this design.
- Only after design lock: implement advanced source pack builder and preview wire.
