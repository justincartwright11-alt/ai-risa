# Upcoming Schedule Queue Consumer Simulation

This deterministic output is based on embedded source fixtures, adapter logic, dependency readiness, batch handoff packaging, runner/queue dry-run staging, queue-bundle planning, emission manifest sequencing, run-cycle ledger, execution decision gate, local queue writing, and queue-consumer simulation logic.

## Total Sink Entries: 1
## Consume-Eligible: 1
## Consume-Blocked: 2
## Simulated Dispatch-Ready: 1
## Withheld: 2

## Dispatch Target Summary
- simulated_dispatch: 1

## Consume Blocker Summary
- not in sink: 2

## Normalized Events

- **ID:** ufc_300 | **Date:** 2026-04-13 | **Promotion:** UFC | **Venue:** T-Mobile Arena | **Sport:** MMA | **Divisions:** Lightweight, Welterweight | **Queue Write Eligible:** True | **Queue Consume Eligible:** True | **Queue Consume Status:** eligible | **Dispatch Simulation ID:** dispatch_sim_queue_write_run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1 | **Dispatch Simulation Status:** ready | **Dispatch Simulation Target:** simulated_dispatch | **Dispatch Simulation Payload:** {'event_id': 'ufc_300', 'handoff_payload_id': 'handoff_ufc_300_UFC_API_v1', 'queue_write_id': 'queue_write_run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1', 'run_cycle_id': 'run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1', 'queue_target': 'queue_ufc_event_batch', 'dispatch_simulation_id': 'dispatch_sim_queue_write_run_cycle_manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1'}
- **ID:** pfl_2026_01 | **Date:** 2026-05-01 | **Promotion:** PFL | **Venue:** unknown | **Sport:** MMA | **Divisions:** Featherweight | **Queue Write Eligible:** False | **Queue Consume Eligible:** False | **Queue Consume Status:** blocked | **Dispatch Simulation ID:** None | **Dispatch Simulation Status:** None | **Dispatch Simulation Target:** None | **Dispatch Simulation Payload:** None
  - Missing: venue
  - Blockers: venue
  - Excluded from handoff: not handoff-ready
- **ID:** one_2026_04 | **Date:** unknown | **Promotion:** ONE | **Venue:** Singapore Indoor Stadium | **Sport:** MMA | **Divisions:** None | **Queue Write Eligible:** False | **Queue Consume Eligible:** False | **Queue Consume Status:** blocked | **Dispatch Simulation ID:** None | **Dispatch Simulation Status:** None | **Dispatch Simulation Target:** None | **Dispatch Simulation Payload:** None
  - Missing: date, divisions
  - Blockers: date, divisions
  - Excluded from handoff: not handoff-ready

This file defines the normalization contract, adapter coverage, dependency readiness, batch handoff packaging, runner staging, queue emission dry-run, queue-bundle planning, emission manifest sequencing, run-cycle ledger, execution decision gate, local queue writing, and queue-consumer simulation format.
