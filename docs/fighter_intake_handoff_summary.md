# Fighter Intake Handoff Summary

## Scope

This workspace owns the holding lane only.

- Ranked intake queue is stored in `fighter_intake_unresolved_queue.csv`.
- Canonical registry writes are not performed here.
- Alias attachment is not performed here.
- Enrichment attachment is not performed here.

## Current Intake State

- Event seeded: `ONE SAMURAI 1`
- Total intake rows: `30`
- Tier 1: `27`
- Tier 2: `0`
- Tier 3: `3`

## Tier Definitions

- Tier 1: full two-name fighters; likely straightforward registry resolution once runtime surfaces are available.
- Tier 2: partial ambiguity; alias or normalization review needed before canonical action.
- Tier 3: single-token or low-confidence identity rows; hold until registry evidence resolves identity.

## Tier 3 Rows

- `Nadaka`
- `Kaito`
- `Hyu`

## Operator Notes

- Intake rows are seeded from `event_coverage_queue.csv` and `one_samurai_1_bouts.csv` only.
- `canonical_fighter_id` remains blank by design in this workspace.
- `enrichment_ref` remains blank by design in this workspace.
- `resolution_tier`, `resolution_group`, and `resolution_notes` are the operator-ready routing fields.
- Do not extend this workspace into canonical writes without the owning `ai_risa_data` runtime surfaces.

## Runtime Handoff

When the `ai_risa_data` runtime surfaces are available, convert the ranked intake queue into:

1. canonical registry creation or match resolution
2. alias attachment and normalization write actions
3. enrichment attachment for resolved fighters