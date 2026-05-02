# AI RISA Premium Report Factory - Button 1 Ranking Runtime Wiring Release Manifest

Slice: ai-risa-premium-report-factory-button1-ranking-runtime-wiring-release-manifest-v1
Date: 2026-05-02
Branch: next-dashboard-polish

## Lane Summary

Button 1 ranking runtime wiring is complete. Preview rows returned by the intake/preview endpoint now carry deterministic, advisory ranking intelligence derived from existing scaffold contracts.

## Commit Chain

| Slice | Commit | Tag |
|---|---|---|
| Design | 18de33a | ai-risa-premium-report-factory-button1-ranking-runtime-wiring-design-v1 |
| Design Review | 6069d23 | ai-risa-premium-report-factory-button1-ranking-runtime-wiring-design-review-v1 |
| Implementation | 762e7bf | ai-risa-premium-report-factory-button1-ranking-runtime-wiring-implementation-v1 |
| Post-Freeze Smoke | a70d767 | ai-risa-premium-report-factory-button1-ranking-runtime-wiring-post-freeze-smoke-v1 |
| Final Review | 585024c | ai-risa-premium-report-factory-button1-ranking-runtime-wiring-final-review-v1 |
| Release Manifest | this commit | ai-risa-premium-report-factory-button1-ranking-runtime-wiring-release-manifest-v1 |

## Files Shipped

| File | Change | Purpose |
|---|---|---|
| `operator_dashboard/prf_ranking_adapter.py` | New | Ranking enrichment adapter — 7 per-engine scorers, bucket logic, reason assembly, `enrich_row_with_ranking()` |
| `operator_dashboard/test_prf_ranking_adapter.py` | New | 41 tests — unit + endpoint integration |
| `operator_dashboard/app.py` | Modified (additive import + 1 call site) | Wires `enrich_row_with_ranking` into `_build_phase1_intake_matchup_preview_row` |

## Released Capability

Button 1 intake/preview endpoint (`POST /api/premium-report-factory/intake/preview`) now returns additive ranking intelligence on every `matchup_previews` row:

### Ranking Scores (per engine)

| Field | Engine | Weight |
|---|---|---|
| `fight_readiness_score` | `ranking.fight_readiness` | 0.22 |
| `report_value_score` | `ranking.report_value` | 0.16 |
| `customer_priority_score` | `ranking.customer_priority` | 0.15 |
| `event_card_priority_score` | `ranking.event_card_priority` | 0.12 |
| `betting_interest_score` | `ranking.betting_interest` | 0.12 |
| `commercial_sellability_score` | `ranking.commercial_sellability` | 0.12 |
| `analysis_confidence_score` | `ranking.analysis_confidence` | 0.11 |

### Composite and Classification

| Field | Description |
|---|---|
| `composite_ranking_score` | Weighted composite, 0–100, deterministic |
| `ranking_bucket` | `priority_tier_1` (≥70) / `priority_tier_2` (≥50) / `watchlist_tier` (≥30) / `low_priority` (<30) / `low_confidence` (validation failure) |
| `ranking_reasons` | Sorted list of deterministic reason codes from locked vocabulary |

### Diagnostics (always included)

| Field | Description |
|---|---|
| `ranking_validation_ok` | Bool — all 7 engine scores present and in range |
| `ranking_missing_inputs` | List of engine IDs absent from scoring |
| `ranking_contract_version` | Adapter version string (`1.0.0`) |

## Locked Configuration

| Item | Value |
|---|---|
| Adapter version | `1.0.0` |
| Bucket: `priority_tier_1` | composite ≥ 70.0 |
| Bucket: `priority_tier_2` | composite ≥ 50.0 |
| Bucket: `watchlist_tier` | composite ≥ 30.0 |
| Bucket: `low_priority` | composite < 30.0 |
| Bucket: `low_confidence` | validation failure |
| Per-engine safe default | 50.0 (neutral mid-range) |
| Reason vocabulary | 9 locked constants |
| Diagnostics included | always |

## Safety Boundaries Preserved

| Boundary | Status |
|---|---|
| No auto-save | ✓ |
| No approval-gate change | ✓ |
| No Button 2 behavior changes | ✓ |
| No Button 3 behavior changes | ✓ |
| No uncontrolled writes | ✓ |
| Existing preview fields unchanged | ✓ |
| Ranking is advisory only | ✓ |
| Additive-only API fields | ✓ |

## Test Results at Lock

| Suite | Result |
|---|---|
| `test_prf_ranking_adapter.py` (41 new) | 41/41 PASS |
| `test_prf_ranking_scaffold.py` | PASS |
| `test_prf_report_export.py` | PASS |
| `test_app_backend.py` | PASS |
| Total | **322/322 PASS** |

## Smoke Results at Lock

7/7 PASS — see `docs/ai_risa_premium_report_factory_button1_ranking_runtime_wiring_post_freeze_smoke_v1.md`

## Final Review Verdict

LANE CLOSED — demo-safe. See `docs/ai_risa_premium_report_factory_button1_ranking_runtime_wiring_final_review_v1.md`
