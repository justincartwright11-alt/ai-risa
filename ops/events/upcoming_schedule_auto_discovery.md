# Upcoming Schedule Local Queue Writer

This deterministic output is based on embedded source fixtures, adapter logic, dependency readiness, batch handoff packaging, runner/queue dry-run staging, queue-bundle planning, emission manifest sequencing, run-cycle ledger, execution decision gate, and local queue writing logic.

## Adapter Coverage
- UFC: 1 event(s)
- PFL: 1 event(s)
- ONE: 1 event(s)

## Total Records: 3
## Go: 1
## Queue-Write Eligible: 1
## Queue-Write Blocked: 2
## Written: 1
## Blocked: 2

## Queue Write Reason Summary
- not execution-go: 2

## Normalized Events

- **ID:** ufc_300 | **Date:** 2026-04-13 | **Promotion:** UFC | **Venue:** T-Mobile Arena | **Sport:** MMA | **Divisions:** Lightweight, Welterweight | **Source:** UFC_API | **Adapter Status:** ok | **Complete:** True | **Run Cycle ID:** run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1 | **Run Cycle Position:** 1 | **Execution Decision:** go | **Execution Go:** True | **Queue Write Eligible:** True | **Queue Write Status:** eligible | **Queue Write ID:** queue_write_run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1 | **Queue Sink Target:** local_sink
- **ID:** pfl_2026_01 | **Date:** 2026-05-01 | **Promotion:** PFL | **Venue:** unknown | **Sport:** MMA | **Divisions:** Featherweight | **Source:** PFL_FEED | **Adapter Status:** ok | **Complete:** False | **Run Cycle ID:** None | **Run Cycle Position:** None | **Execution Decision:** no_go | **Execution Go:** False | **Queue Write Eligible:** False | **Queue Write Status:** blocked | **Queue Write ID:** None | **Queue Sink Target:** None
  - Missing: venue
  - Blockers: venue
  - Excluded from handoff: not handoff-ready
- **ID:** one_2026_04 | **Date:** unknown | **Promotion:** ONE | **Venue:** Singapore Indoor Stadium | **Sport:** MMA | **Divisions:** None | **Source:** ONE_CHAMPIONSHIP | **Adapter Status:** incomplete | **Complete:** False | **Run Cycle ID:** None | **Run Cycle Position:** None | **Execution Decision:** no_go | **Execution Go:** False | **Queue Write Eligible:** False | **Queue Write Status:** blocked | **Queue Write ID:** None | **Queue Sink Target:** None
  - Missing: date, divisions
  - Blockers: date, divisions
  - Excluded from handoff: not handoff-ready

This file defines the normalization contract, adapter coverage, dependency readiness, batch handoff packaging, runner staging, queue emission dry-run, queue-bundle planning, emission manifest sequencing, run-cycle ledger, execution decision gate, and local queue writing format.
