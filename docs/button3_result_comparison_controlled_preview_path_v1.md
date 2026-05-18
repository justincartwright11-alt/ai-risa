# button3-result-comparison-controlled-preview-path-v1

## Objective
Implement a governed preview-only Button 3 result-comparison path that compares AI-RISA prediction fields against confirmed results without opening any apply/mutation behavior.

## Route
- Added: `POST /api/button3/result-comparison/preview-v1`
- Purpose: return comparison preview payload with required status/classification fields.
- Governance: preview-only; mutation/learning/calibration/queue flags remain false.

## Supported Comparison Statuses
- `result_found`
- `no_result_found`
- `needs_source`
- `conflict`
- `ready_to_compare`
- `needs_manual_review`

## Required Fields Included
- `fight_id`
- `event_name`
- `fighter_a`
- `fighter_b`
- `predicted_winner`
- `predicted_method`
- `predicted_round`
- `actual_winner`
- `actual_method`
- `actual_round`
- `result_source_url`
- `source_tier`
- `comparison_status`
- `accuracy_preview`
- `operator_review_required`
- `mutation_performed=false`
- `learning_apply_performed=false`
- `calibration_write_performed=false`
- `queue_write_performed=false`
- `button3_mutation_performed=false`

## Accuracy Preview
`accuracy_preview` includes:
- `winner`: hit/miss/unavailable
- `method`: hit/miss/unavailable
- `round`: hit/miss/unavailable
- `overall`: hit/miss/partial/unavailable
- `winner_match` bool
- `method_mismatch` bool
- `round_mismatch` bool

## Dashboard Surface
Added display-only preview language/surface in Button 3 panel:
- explicit preview-only statement
- no apply/learning/calibration buttons
- field list for controlled comparison preview output

## Scope Safety
No changes to:
- Button 1 discovery path
- Button 2 generation path
- queue mutation
- learning/calibration apply paths
- external delivery/API behavior

No auto-result fill and no fake result generation introduced.
