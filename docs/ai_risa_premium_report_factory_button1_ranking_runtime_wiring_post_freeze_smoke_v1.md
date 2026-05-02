# AI RISA Premium Report Factory - Button 1 Ranking Runtime Wiring Post-Freeze Smoke

Slice: ai-risa-premium-report-factory-button1-ranking-runtime-wiring-post-freeze-smoke-v1
Date: 2026-05-02
Branch: next-dashboard-polish
Type: docs-only smoke artifact

## Baseline

- Implementation commit: 762e7bf
- Implementation tag: ai-risa-premium-report-factory-button1-ranking-runtime-wiring-implementation-v1
- Working tree at smoke time: clean
- Runtime artifacts committed: none

## Smoke Execution Method

Inline Python smoke script executed against Flask test client (no file created, no server required).
All checks run in a single session against `app.config['TESTING'] = True`.

## Smoke Results

| # | Check | Result |
|---|---|---|
| 1 | Discovery/preview rows include all 10 ranking fields and 3 diagnostic fields | PASS |
| 2 | Existing preview fields (`fighter_a`, `fighter_b`, `bout_order`, `weight_class`, `ruleset`, `source_reference`, `parse_status`, `parse_notes`, `temporary_matchup_id`) unchanged | PASS |
| 3 | Composite ranking and `ranking_reasons` are deterministic (two independent calls, same input, identical output) | PASS |
| 4 | `ranking_bucket` and `ranking_reasons` populated and valid | PASS |
| 5 | Save endpoint rejects empty payload (`ok=False`, `saved_count=0`) — operator approval still required | PASS |
| 6 | Button 2 `compare-with-result` endpoint responds normally (`status=200`) — no behavior drift | PASS |
| 7 | Working tree clean after smoke — no runtime artifacts committed | PASS |

**Overall: 7/7 PASS**

## Check 4 Detail

```
ranking_bucket: priority_tier_2
ranking_reasons: [
  card_position_early,
  parse_complete,
  ruleset_unknown,
  source_reference_present,
  weight_class_unknown
]
```

Bucket is within the locked vocabulary (`priority_tier_1`, `priority_tier_2`, `watchlist_tier`, `low_priority`, `low_confidence`).
Reasons are sorted, deterministic, and drawn exclusively from the locked reason vocabulary.

## Check 5 Detail

```
POST /api/premium-report-factory/queue/save-selected  body={}
Response: ok=False  saved_count=0
```

Approval gate is intact. No rows were saved without operator selection.

## Scope Confirmation at Smoke Time

- Button 1 preview rows: additive ranking fields present ✓
- Button 2 behavior: unchanged ✓
- Button 3 behavior: not exercised (out of scope) ✓
- Writes: none introduced by ranking enrichment ✓
- Auto-save: not triggered ✓
- Approval gate: active ✓

## Verdict

**SMOKE PASSED. Implementation baseline `762e7bf` is demo-safe.**

## Next Safe Slice

ai-risa-premium-report-factory-button1-ranking-runtime-wiring-final-review-v1
