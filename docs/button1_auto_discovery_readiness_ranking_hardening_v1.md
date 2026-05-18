# button1-auto-discovery-readiness-ranking-hardening-v1

## Objective
Add governed Button 1 auto-discovery readiness ranking so operators can prioritize source-backed event cards and matchups for queue-save review.

## What Changed
- Added ranking engine module:
  - `operator_dashboard/button1_auto_discovery_readiness_ranking_v1.py`
- Wired ranking enrichment into Button 1 runtime context payload candidate rows:
  - `operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py`
- Updated Button 1 dashboard event-card render surface to display ranking metadata:
  - rank
  - readiness band
  - readiness score
  - recommended operator action
  - key reasons

## Ranking Signals Used
- source_tier
- provenance_status
- card_completeness_status
- matchup_count
- button2_readiness_status
- queue_save_eligible
- event_date proximity
- promotion priority
- sport/modality
- source_url present
- fighter names present
- duplicate/conflict flags
- needs_review and secondary-confirmation flags

## Required Output Fields Added
- discovery_rank
- readiness_score
- readiness_band (`high|medium|low|blocked`)
- ranking_reasons[]
- blocking_reasons[]
- recommended_operator_action (`save_to_queue|review_source|review_identity|wait_for_more_card_data|blocked`)
- source_quality_score
- completeness_score
- button2_report_readiness_score

## Governance
- Preview-only ranking enrichment.
- No auto-save.
- No queue write unless existing explicit Gate 1 approval path is used.
- No PDF generation.
- No delivery.
- No Button 2 behavior changes.
- No Button 3 mutation.
- No learning/calibration mutation.
- No fake sources/matchups.
- Source-backed provenance requirement preserved.

## Dashboard Result
Button 1 Source-Backed Event Cards now surface rank/readiness/action/reasons to guide operator priority while keeping save and generation behavior unchanged.
