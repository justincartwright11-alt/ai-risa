# Upcoming Schedule Dispatch Outcome Ledger

This deterministic output is based on embedded source fixtures, adapter logic, dependency readiness, batch handoff packaging, runner/queue dry-run staging, queue-bundle planning, emission manifest sequencing, run-cycle ledger, execution decision gate, local queue writing, queue-consumer simulation, and dispatch outcome ledger logic.

## Total Sink Entries: 1
## Consume-Eligible: 1
## Consume-Blocked: 2
## Simulated Dispatch-Ready: 1
## Withheld: 2
## Simulated Dispatch Outcome: 1
## Not Dispatched: 2

## Acknowledgement State Summary
- acked: 1
- not_applicable: 2

## Retry Class Distribution
- none: 1

## Ledger Record Summary
- Recorded: 1
- Not Recorded: 2

## Dispatch Target Summary
- simulated_dispatch: 1

## Consume Blocker Summary
- not in sink: 2

## Normalized Events

- **ID:** ufc_300 | **Date:** 2026-04-13 | **Promotion:** UFC | **Venue:** T-Mobile Arena | **Sport:** MMA | **Divisions:** Lightweight, Welterweight | **Queue Write Eligible:** True | **Queue Consume Eligible:** True | **Queue Consume Status:** eligible | **Dispatch Simulation ID:** dispatch_sim_queue_write_run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1 | **Dispatch Simulation Status:** ready | **Dispatch Simulation Target:** simulated_dispatch | **Dispatch Simulation Payload:** {'event_id': 'ufc_300', 'handoff_payload_id': 'handoff_ufc_300_UFC_API_v1', 'queue_write_id': 'queue_write_run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1', 'run_cycle_id': 'run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1', 'queue_target': 'queue_ufc_event_batch', 'dispatch_simulation_id': 'dispatch_sim_queue_write_run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1'} | **Dispatch Outcome:** simulated_success | **Retry Class:** none | **Retry Eligible:** False | **Ack State:** acked | **Ledger Recorded:** True | **Ledger Record ID:** ledger_dispatch_sim_queue_write_run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1
- **ID:** pfl_2026_01 | **Date:** 2026-05-01 | **Promotion:** PFL | **Venue:** unknown | **Sport:** MMA | **Divisions:** Featherweight | **Queue Write Eligible:** False | **Queue Consume Eligible:** False | **Queue Consume Status:** blocked | **Dispatch Simulation ID:** None | **Dispatch Simulation Status:** None | **Dispatch Simulation Target:** None | **Dispatch Simulation Payload:** None | **Dispatch Outcome:** not_dispatched | **Retry Class:** None | **Retry Eligible:** False | **Ack State:** not_applicable | **Ledger Recorded:** False | **Ledger Record ID:** None
  - Missing: venue
  - Blockers: venue
  - Excluded from handoff: not handoff-ready
- **ID:** one_2026_04 | **Date:** unknown | **Promotion:** ONE | **Venue:** Singapore Indoor Stadium | **Sport:** MMA | **Divisions:** None | **Queue Write Eligible:** False | **Queue Consume Eligible:** False | **Queue Consume Status:** blocked | **Dispatch Simulation ID:** None | **Dispatch Simulation Status:** None | **Dispatch Simulation Target:** None | **Dispatch Simulation Payload:** None | **Dispatch Outcome:** not_dispatched | **Retry Class:** None | **Retry Eligible:** False | **Ack State:** not_applicable | **Ledger Recorded:** False | **Ledger Record ID:** None
  - Missing: date, divisions
  - Blockers: date, divisions
  - Excluded from handoff: not handoff-ready

This file defines the normalization contract, adapter coverage, dependency readiness, batch handoff packaging, runner staging, queue emission dry-run, queue-bundle planning, emission manifest sequencing, run-cycle ledger, execution decision gate, local queue writing, queue-consumer simulation, and dispatch outcome ledger format.
