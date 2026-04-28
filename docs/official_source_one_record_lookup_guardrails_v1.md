# official-source-one-record-lookup-guardrails-v1

## 1. Purpose
Define a safe, implementation-ready guardrail design for one-record official-source actual-result lookup.

This slice is design-only and introduces no code, no runtime wiring, and no behavior changes.

## 2. Non-goals
- No backend endpoint implementation.
- No UI implementation or event wiring.
- No web lookup execution.
- No batch lookup or batch write support.
- No scoring formula or scoring semantics changes.
- No prediction logic changes.
- No event intake rule changes.
- No mutation of `ops/accuracy/actual_results.json`, `ops/accuracy/actual_results_manual.json`, or `ops/accuracy/actual_results_unresolved.json`.

## 3. Allowed sources
Allowed source classes for external confirmation (after explicit operator action only):
- Tier A (official): promotion or sanctioning body domains.
  - `ufc.com`
  - `onefc.com`
  - `glorykickboxing.com`
  - `toprank.com`
  - `matchroomboxing.com`
  - `queensberry.co.uk`
  - `nolimitboxing.com.au`
- Tier B (highly reliable secondary, review-gated):
  - `espn.com`
  - `tapology.com`
  - `sherdog.com`
  - `boxrec.com`
  - `mmadecisions.com`

Design rule: Tier B can support preview evidence, but must default to manual review unless corroborated by Tier A or operator-approved conflict resolution.

## 4. Disallowed sources
- Social posts as sole source (X, Instagram, Facebook, Reddit, etc.).
- User-generated forums, blogs, or scraping mirrors with unknown provenance.
- AI summaries without direct source citation.
- Any source without stable URL/title/date metadata.

## 5. One-record-only rule
Request must include exactly one `selected_key`.

Validation:
- Missing key -> 400.
- Empty key -> 400.
- List or multi-key payload -> 400.
- Any attempt to submit more than one target -> 400.

## 6. No batch rule
The official-source lookup design is strictly single-record.

Disallowed:
- Multi-record arrays.
- Iterative auto-processing over waiting rows.
- Queue-wide lookup triggers.

## 7. Operator approval model
Two-step approval model (consistent with guarded local apply patterns):
- Step A: preview/dry-run only (`approval_granted=false`).
- Step B: explicit approval required before any write (`approval_granted=true`).

Write path remains blocked unless all guardrails pass.

## 8. Dry-run before lookup model
Dry-run is mandatory and must execute before external lookup is permitted.

Dry-run responsibilities:
- Validate selected key exists in waiting rows.
- Check local actuals first.
- Determine whether external lookup is eligible.
- Return proposed action and manual-review flags.
- Guarantee `mutation_performed=false`.

If local actual is already found with sufficient confidence, external lookup should be skipped and response should indicate no external action required.

## 9. Request schema
Proposed design contract (for future implementation):

```json
{
  "selected_key": "string (required, exactly one)",
  "mode": "official_source_one_record",
  "approval_granted": false,
  "lookup_intent": "preview_only | execute_lookup | apply_write",
  "operator_note": "string (optional)"
}
```

Rules:
- `mode` must be exact.
- `lookup_intent` required for explicit phase control.
- `approval_granted` required and must be `false` for preview phase.

## 10. Response schema
Proposed response shape aligned to current guarded payload patterns:

```json
{
  "ok": true,
  "mode": "official_source_one_record",
  "selected_key": "string",
  "approval_required": true,
  "approval_granted": false,
  "phase": "dry_run | lookup_preview | apply",
  "local_result_found": false,
  "external_lookup_performed": false,
  "bulk_lookup_performed": false,
  "mutation_performed": false,
  "manual_review_required": true,
  "scoring_semantics_changed": false,
  "selected_row": {},
  "proposed_write": null,
  "source_citation": {
    "url": "",
    "title": "",
    "published_or_event_date": "",
    "source_confidence": "none | official | secondary | conflict"
  },
  "audit": {
    "write_target": null,
    "write_action": "insert_or_update_single_record",
    "selected_key": "string",
    "record_fight_id": "string|null",
    "before_row_count": null,
    "after_row_count": null,
    "write_performed": false,
    "correlation_id": "string",
    "operator_note": "string"
  },
  "message": "string"
}
```

## 11. Manual-review states
Manual review must be required for any of the following:
- `selected_key` not found.
- Local result missing and no acceptable external citation.
- Source conflict (different winners across sources).
- Identity conflict (fighter/event mismatch ambiguity).
- Source confidence below threshold.
- Missing source citation fields.
- Any parsing ambiguity in winner/method/round.

## 12. Audit fields
Minimum audit envelope (building on existing guarded-single audit style):
- `correlation_id`
- `selected_key`
- `record_fight_id`
- `phase`
- `approval_required`
- `approval_granted`
- `local_result_found`
- `external_lookup_performed`
- `source_url`
- `source_title`
- `source_date`
- `source_confidence`
- `write_target`
- `before_row_count`
- `after_row_count`
- `write_performed`
- `reason_code`
- `message`

## 13. Failure states
Proposed deterministic failures:
- 400: invalid schema, invalid mode, missing selected key, multi-key request, invalid phase transition.
- 404: selected key not found.
- 409: source conflict, identity conflict, stale approval token (if tokening is later adopted).
- 422: citation incomplete or confidence below required threshold.
- 500: internal processing error (no partial write, no silent fallback).

All failures must return:
- `mutation_performed=false`
- `bulk_lookup_performed=false`
- `scoring_semantics_changed=false`
- explicit `reason_code`

## 14. Rate-limit and timeout rules
For future implementation defaults:
- One-record external lookup only.
- Max external source pages per request: 3 official-first, then optional 2 secondary.
- Per-source timeout: 6 seconds.
- Total request timeout budget: 20 seconds.
- No automatic retries.
- No background polling.

## 15. Source-citation requirements
External result evidence is valid only when all are present:
- Source URL
- Source title (or authoritative page label)
- Source date (published date or event date)
- Extracted winner value

If any required citation field is missing, response is rejected for apply and forced to manual review.

## 16. No-mutation guarantees
Design guarantees for preview and lookup phases:
- `mutation_performed=false`
- no writes to any `actual_results*.json`
- no score recalculation side effects
- no queue status mutation
- no prediction record mutation

Write phase (future implementation) must remain approval-gated and single-record only.

## 17. Future implementation slices
Recommended implementation sequence after design review:
1. Contract-only endpoint scaffold with strict schema validation (no lookup).
2. Local-first dry-run integration using existing waiting-row and local-map helpers.
3. Official-source citation parser integration behind explicit operator action.
4. Approval-gated single-write path with audit enrichment.
5. UI wiring slice (separate, post-backend validation).
6. Observability slice (metrics, rate-limit counters, failure reason histograms).

## 18. Test plan
Required tests before enabling any runtime wiring:
- Contract tests:
  - reject missing/empty/multi-key payloads.
  - reject mode mismatch.
  - reject apply without prior approval flow.
- Guardrail tests:
  - local-first check always runs before external lookup.
  - no page-load invocation.
  - no batch invocation accepted.
  - no retry behavior.
- Citation tests:
  - reject missing URL/title/date.
  - require confidence classification.
  - force manual review on conflict/ambiguity.
- Mutation safety tests:
  - verify no writes in dry-run and lookup-preview phases.
  - verify `scoring_semantics_changed=false` always.
- Audit tests:
  - ensure required audit fields are present on success and failure.
- UI contract tests (future UI slice):
  - apply disabled until approval.
  - no auto-lookup on page load.

---

Design status: draft complete for review.
Implementation status: not started (intentionally).
