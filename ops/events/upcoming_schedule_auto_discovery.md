# Upcoming Schedule Execution Decision Gate

This deterministic output is based on embedded source fixtures, adapter logic, dependency readiness, batch handoff packaging, runner/queue dry-run staging, queue-bundle planning, emission manifest sequencing, run-cycle ledger, and execution decision gate logic.

## Adapter Coverage
- UFC: 1 event(s)
- PFL: 1 event(s)
- ONE: 1 event(s)

## Total Records: 3
## Ledger Included: 1
## Go: 1
## Conditional: 0
## No-Go: 2
## Gate Level Distribution: open=1, conditional=0, blocked=2

## Blocked Reason Summary
- not ledger-included: 2

## Final Cycle Decision Summary
- Go: 1
- Blocked: 2
- Open: 1
- Conditional: 0
- Blocked: 2

## Normalized Events

- **ID:** ufc_300 | **Date:** 2026-04-13 | **Promotion:** UFC | **Venue:** T-Mobile Arena | **Sport:** MMA | **Divisions:** Lightweight, Welterweight | **Source:** UFC_API | **Adapter Status:** ok | **Complete:** True | **Run Cycle ID:** run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1 | **Run Cycle Position:** 1 | **Execution Gate Status:** open | **Ledger Included:** True | **Execution Decision:** go | **Execution Go:** True | **Execution Blocked:** False | **Execution Gate Level:** open | **Execution Decision Reasons:** [] | **Ledger Summary:** {'total_records': 3, 'staged_records': 1, 'bundles': 1, 'manifest_entries': 1, 'ledger_included': 1, 'blocked_records': 2} | **Execution Gate Summary:** {'total': 3, 'go': 1, 'conditional': 0, 'no_go': 2, 'open_levels': 1, 'conditional_levels': 0, 'blocked_levels': 2, 'reasons': {'not ledger-included': 2}}
- **ID:** pfl_2026_01 | **Date:** 2026-05-01 | **Promotion:** PFL | **Venue:** unknown | **Sport:** MMA | **Divisions:** Featherweight | **Source:** PFL_FEED | **Adapter Status:** ok | **Complete:** False | **Run Cycle ID:** None | **Run Cycle Position:** None | **Execution Gate Status:** open | **Ledger Included:** False | **Execution Decision:** no_go | **Execution Go:** False | **Execution Blocked:** True | **Execution Gate Level:** blocked | **Execution Decision Reasons:** ['not ledger-included'] | **Ledger Summary:** {'total_records': 3, 'staged_records': 1, 'bundles': 1, 'manifest_entries': 1, 'ledger_included': 1, 'blocked_records': 2} | **Execution Gate Summary:** {'total': 3, 'go': 1, 'conditional': 0, 'no_go': 2, 'open_levels': 1, 'conditional_levels': 0, 'blocked_levels': 2, 'reasons': {'not ledger-included': 2}}
  - Missing: venue
  - Blockers: venue
  - Excluded from handoff: not handoff-ready
- **ID:** one_2026_04 | **Date:** unknown | **Promotion:** ONE | **Venue:** Singapore Indoor Stadium | **Sport:** MMA | **Divisions:** None | **Source:** ONE_CHAMPIONSHIP | **Adapter Status:** incomplete | **Complete:** False | **Run Cycle ID:** None | **Run Cycle Position:** None | **Execution Gate Status:** open | **Ledger Included:** False | **Execution Decision:** no_go | **Execution Go:** False | **Execution Blocked:** True | **Execution Gate Level:** blocked | **Execution Decision Reasons:** ['not ledger-included'] | **Ledger Summary:** {'total_records': 3, 'staged_records': 1, 'bundles': 1, 'manifest_entries': 1, 'ledger_included': 1, 'blocked_records': 2} | **Execution Gate Summary:** {'total': 3, 'go': 1, 'conditional': 0, 'no_go': 2, 'open_levels': 1, 'conditional_levels': 0, 'blocked_levels': 2, 'reasons': {'not ledger-included': 2}}
  - Missing: date, divisions
  - Blockers: date, divisions
  - Excluded from handoff: not handoff-ready

This file defines the normalization contract, adapter coverage, dependency readiness, batch handoff packaging, runner staging, queue emission dry-run, queue-bundle planning, emission manifest sequencing, run-cycle ledger, and execution decision gate format.
