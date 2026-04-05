# Upcoming Schedule Run Cycle Ledger

This deterministic output is based on embedded source fixtures, adapter logic, dependency readiness, batch handoff packaging, runner/queue dry-run staging, queue-bundle planning, emission manifest sequencing, and run-cycle ledger logic.

## Adapter Coverage
- UFC: 1 event(s)
- PFL: 1 event(s)
- ONE: 1 event(s)

## Total Records: 3
## Staged Records: 1
## Queue Bundles: 1
## Manifest Entries: 1
## Ledger Included: 1
## Execution Gate: open

## Run Order Summary
- run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1 (run_cycle_position=1)

## Blocked Reasons Summary
- pfl_2026_01: []
- one_2026_04: []

## Normalized Events

- **ID:** ufc_300 | **Date:** 2026-04-13 | **Promotion:** UFC | **Venue:** T-Mobile Arena | **Sport:** MMA | **Divisions:** Lightweight, Welterweight | **Source:** UFC_API | **Adapter Status:** ok | **Complete:** True | **Run Cycle ID:** run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1 | **Run Cycle Position:** 1 | **Execution Gate Status:** open | **Ledger Included:** True | **Ledger Summary:** {'total_records': 3, 'staged_records': 1, 'bundles': 1, 'manifest_entries': 1, 'ledger_included': 1, 'blocked_records': 2}
- **ID:** pfl_2026_01 | **Date:** 2026-05-01 | **Promotion:** PFL | **Venue:** unknown | **Sport:** MMA | **Divisions:** Featherweight | **Source:** PFL_FEED | **Adapter Status:** ok | **Complete:** False | **Run Cycle ID:** None | **Run Cycle Position:** None | **Execution Gate Status:** open | **Ledger Included:** False | **Ledger Summary:** {'total_records': 3, 'staged_records': 1, 'bundles': 1, 'manifest_entries': 1, 'ledger_included': 1, 'blocked_records': 2}
  - Missing: venue
  - Blockers: venue
  - Excluded from handoff: not handoff-ready
- **ID:** one_2026_04 | **Date:** unknown | **Promotion:** ONE | **Venue:** Singapore Indoor Stadium | **Sport:** MMA | **Divisions:** None | **Source:** ONE_CHAMPIONSHIP | **Adapter Status:** incomplete | **Complete:** False | **Run Cycle ID:** None | **Run Cycle Position:** None | **Execution Gate Status:** open | **Ledger Included:** False | **Ledger Summary:** {'total_records': 3, 'staged_records': 1, 'bundles': 1, 'manifest_entries': 1, 'ledger_included': 1, 'blocked_records': 2}
  - Missing: date, divisions
  - Blockers: date, divisions
  - Excluded from handoff: not handoff-ready

This file defines the normalization contract, adapter coverage, dependency readiness, batch handoff packaging, runner staging, queue emission dry-run, queue-bundle planning, emission manifest sequencing, and run-cycle ledger format.
