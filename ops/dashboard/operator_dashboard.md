# AI-RISA Operator Dashboard (Slice 1)

Generated (UTC): 2026-04-01T08:32:49.395086+00:00

## Latest Pipeline Snapshot
- Status: success
- Stage: full_pipeline
- Started At: 2026-04-01T19:12:29.740257
- Finished At: 2026-04-01T19:12:29.943647
- Warnings: 5
- Errors: 0
- Summary Path: output/full_pipeline_run_summary.json

## Coverage Snapshot
- Source: output/full_pipeline_run_summary.json
- Analysis Coverage: {'stages_total': 6, 'stages_analyzed': 2, 'stages_soft_skipped': 4, 'analyzed_stage_names': ['schedule', 'batch'], 'skipped_stage_names': ['ingest', 'resolver', 'queue_build', 'queue_run']}

## Skipped/Exclusions Snapshot
- Source: output/full_pipeline_run_summary.json
- Skipped/Exclusions: {'warning_type_counts': {'dry_run_soft_skip': 4, 'enrichment_diagnostic': 1}, 'enrichment_reason_rollup': {'resolver:skipped_tba': 5}}

## Warning Interpretation Snapshot
- Source: output/full_pipeline_run_summary.json
- Operator Interpretation: {'note': 'Dry-run completed. Warnings are expected soft-skip notices and coverage indicators, not execution failures.', 'warning_non_fatal': True}
- Warning Readability: {'informational_count': 4, 'non_fatal_operational_count': 1, 'action_needed_count': 0, 'informational_examples': [{'type': 'dry_run_soft_skip', 'stage': 'ingest', 'reason': None, 'count': None, 'message': "Stage 'ingest' was skipped by dry-run policy; this is informational."}, {'type': 'dry_run_soft_skip', 'stage': 'resolver', 'reason': None, 'count': None, 'message': "Stage 'resolver' was skipped by dry-run policy; this is informational."}, {'type': 'dry_run_soft_skip', 'stage': 'queue_build', 'reason': None, 'count': None, 'message': "Stage 'queue_build' was skipped by dry-run policy; this is informational."}, {'type': 'dry_run_soft_skip', 'stage': 'queue_run', 'reason': None, 'count': None, 'message': "Stage 'queue_run' was skipped by dry-run policy; this is informational."}], 'non_fatal_operational_examples': [{'type': 'enrichment_diagnostic', 'stage': 'resolver', 'reason': 'skipped_tba', 'count': 5, 'message': "resolver reported 5 item(s) for enrichment diagnostic 'skipped_tba'."}], 'action_needed_examples': []}

## Recommended Operator Action
- Proceed with outputs while monitoring documented exclusions and non-fatal warning trends.

## Source Summaries
- full_pipeline: path=output/full_pipeline_run_summary.json exists=True status=success stage=full_pipeline finished_at=2026-04-01T19:12:29.943647
- event_batch: path=output/event_batch_run_summary.json exists=True status=success stage=batch finished_at=2026-04-01T18:34:00.552635
- event_batch_dry_run: path=output/dry_run/event_batch_run_summary.json exists=True status=success stage=batch finished_at=2026-04-01T19:12:29.928425
- prediction_queue_run: path=output/prediction_queue_run_summary.json exists=True status=success stage=prediction_queue_run finished_at=2026-04-01T18:41:35.965039
