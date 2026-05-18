# button1-full-card-feed-dashboard-runtime-confirmation-v1

## Scope
- Runtime confirmation for real Button 1 dashboard feed path only.
- Proves full-card event rows from approved source feed renderable through the Button 1 UI runtime contract.
- Preserves preview-only governance with no write, no delivery, and no learning/calibration mutation.

## Runtime Confirmation Target
- Dashboard route: `/`
- Workflow runtime endpoint: `/api/local-ai/orchestrator/workflow-preview`
- Source button: `button1_find_fights`
- Runtime mode: `use_runtime_context=true`, `execute_preview=true`

## Full-Card Confirmation Evidence
All four event cards are present in runtime payload and remain `full_card_confirmed`:

1. Boxing - Joshua vs Dubois
   - `card_completeness_status=full_card_confirmed`
   - `matchup_count=5`
2. MMA - UFC 300
   - `card_completeness_status=full_card_confirmed`
   - `matchup_count=5`
3. Kickboxing - GLORY 100
   - `card_completeness_status=full_card_confirmed`
   - `matchup_count=5`
4. Muay Thai - ONE SAMURAI 1
   - `card_completeness_status=full_card_confirmed`
   - `matchup_count=15`

## Button 1 UI Visibility Contract Proof
- Dashboard HTML exposes Source-Backed Event Cards panel.
- UI script keeps runtime wire: `requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_FIND_FIGHTS)`.
- Event card renderer displays:
  - Card completeness label (`Card Completeness`)
  - Matchup count label (`Matchup Count`)
  - Per-matchup selection controls (`Select for PDF`)

## Governance Proof
- `preview_only=true`
- `approval_required=true`
- `source_backed=true`
- valid `source_url` present (event + matchup rows)
- Tier-A queue-save eligibility preserved for Boxing/MMA/Kickboxing matchups
- Muay Thai remains gated (`requires_secondary_confirmation=true`, `unsafe_queue_save_blocked=true`)
- No auto-save, no PDF generation, no delivery, no learning/calibration

## Validation
- `operator_dashboard/test_button1_full_card_feed_dashboard_runtime_confirmation_v1.py`
- `operator_dashboard/test_button1_full_card_feed_dashboard_runtime_confirmation_v1.py` -> 5/5 passed
- Focused Button 1 regression bundle -> 43/43 passed
- Live dashboard runtime check at `http://127.0.0.1:5050/` -> passed

## Artifacts
- `docs/button1_full_card_feed_dashboard_runtime_confirmation_v1.md`
- `ops/release_checks/button1_full_card_feed_dashboard_runtime_confirmation_v1/dashboard_runtime_confirmation_summary.json`
