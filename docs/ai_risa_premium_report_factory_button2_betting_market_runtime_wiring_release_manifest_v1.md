# AI RISA Premium Report Factory — Button 2 Betting Market Runtime Wiring: Release Manifest v1

Slice: ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-release-manifest-v1  
Date: 2026-05-03  
Branch: next-dashboard-polish

---

## Lane Summary

Button 2 betting-market runtime wiring is complete. The premium report factory generate endpoint now supports an optional betting-analyst mode that appends 12 additive analytical fields to each report object when activated. Core report generation, all existing gates, and Button 1/3 behavior are entirely unchanged.

---

## Commit Chain

| Slice | Commit | Tag |
|-------|--------|-----|
| Design | `61528a9` | `ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-design-v1` |
| Design Review | `d893eed` | `ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-design-review-v1` |
| Implementation | `bbd5ced` | `ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-implementation-v1` |
| Post-Freeze Smoke | `c82e89f` | `ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-post-freeze-smoke-v1` |
| Final Review | `fb63fd0` | `ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-final-review-v1` |
| Release Manifest | this commit | `ai-risa-premium-report-factory-button2-betting-market-runtime-wiring-release-manifest-v1` |

---

## Files Shipped

| File | Change | Purpose |
|------|--------|---------|
| `operator_dashboard/prf_betting_market_adapter.py` | New | Betting-market enrichment adapter — odds ingestion, implied probability, fair price estimation, market edge, volatility grade, pass/no-bet logic, mandatory disclaimer, `build_betting_market_enrichment()` |
| `operator_dashboard/test_prf_betting_market_adapter.py` | New | 5 adapter-level tests — disclaimer, missing odds, no guaranteed profit, pass/no-bet, required fields |
| `operator_dashboard/prf_report_builder.py` | Modified (additive) | Accepts `betting_analyst_mode=False` in `generate_reports()`; appends betting enrichment after all existing gates when mode active |
| `operator_dashboard/app.py` | Modified (additive) | Reads `betting_analyst_mode` or `report_mode="betting_analyst"` from generate request; passes resolved boolean to `generate_reports()` |

---

## Released Capability

Button 2 generate endpoint (`POST /api/premium-report-factory/reports/generate`) now accepts `betting_analyst_mode: true` (or `report_mode: "betting_analyst"`) in the request body. When active, each report object in the response is enriched with the following additive fields:

### Status and Source

| Field | Description |
|-------|-------------|
| `betting_market_status` | `ready` / `partial` / `unavailable` — reflects data completeness, never blocks generation |
| `odds_source_status` | `verified_snapshot` / `snapshot_attached` / `absent` |
| `betting_missing_inputs` | Sorted list of missing input identifiers |

### Analytical Outputs

| Field | Description |
|-------|-------------|
| `implied_probability` | `{fighter_a, fighter_b}` derived from moneyline pair; `null` when odds absent |
| `fair_price_estimate` | `{fighter_a_fair_probability, fighter_b_fair_probability}` from model confidence; `null` when confidence unavailable |
| `market_edge_summary` | `{fighter_a_edge, fighter_b_edge, note}`; `null` when either implied prob or fair price absent |
| `volatility_grade` | `high` / `medium` / `low` / `unstable` / `null`; deterministic thresholds locked |
| `round_band_betting_path` | Truncated round-by-round path string for analyst context; `null` when absent |
| `prop_market_notes` | List of analyst context strings about prop pathway confidence |

### Governance (always present when mode active)

| Field | Description |
|-------|-------------|
| `pass_no_bet_conditions` | Non-empty list of deterministic no-bet triggers |
| `betting_risk_disclaimer` | Canonical disclaimer: "Analytical content only. No wagering advice, no guaranteed outcomes, and no automated betting execution." |
| `betting_engine_contributions` | `[{engine_id, status}]` for all 10 betting engines |

---

## Locked Configuration

| Item | Value |
|------|-------|
| Volatility grade: high | `max_edge ≥ 0.10` |
| Volatility grade: medium | `max_edge ≥ 0.05` |
| Volatility grade: low | `max_edge < 0.05` |
| Volatility grade: unstable | missing inputs, no edge computable |
| No-bet edge threshold | `max_edge < 0.02` |
| Disclaimer constant | `BETTING_RISK_DISCLAIMER_TEXT` |
| Betting engines tracked | 10 (`betting.odds_ingestion` → `betting.risk_disclaimer`) |
| Mode selector (request) | `betting_analyst_mode: true` OR `report_mode: "betting_analyst"` |

---

## Safety Boundaries Preserved

| Boundary | Status |
|----------|--------|
| No live odds fetching | ✓ |
| No betting automation or execution | ✓ |
| No staking or wager management | ✓ |
| No writes to any store | ✓ |
| No learning or calibration changes | ✓ |
| No Button 1 behavior changes | ✓ |
| No Button 3 behavior changes | ✓ |
| Readiness/sparse/combat gates unchanged | ✓ |
| Additive-only API fields | ✓ |
| Betting fields absent when mode not selected | ✓ |
| No guaranteed-profit language | ✓ |

---

## Test Results at Lock

| Suite | Tests | Result |
|-------|-------|--------|
| `test_prf_betting_market_adapter.py` (adapter-level) | 5 | PASS |
| `test_app_backend.py` — Button 2 betting tests | 6 | PASS |
| `test_app_backend.py` — Button 3 anti-drift | 3 | PASS |
| `test_prf_ranking_adapter.py` — Button 1 anti-drift | 41 | PASS |
| Lane total | **55** | **ALL PASS** |
| Full lane suites combined | **323** | **ALL PASS** |

---

## Smoke Results at Lock

8/8 PASS — see [docs/ai_risa_premium_report_factory_button2_betting_market_runtime_wiring_post_freeze_smoke_v1.md](ai_risa_premium_report_factory_button2_betting_market_runtime_wiring_post_freeze_smoke_v1.md)

---

## Final Review Verdict

LANE CLOSED — demo-safe. See [docs/ai_risa_premium_report_factory_button2_betting_market_runtime_wiring_final_review_v1.md](ai_risa_premium_report_factory_button2_betting_market_runtime_wiring_final_review_v1.md)
