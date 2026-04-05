# Upcoming Schedule Bundle Emission Manifest

This deterministic output is based on embedded source fixtures, adapter logic, dependency readiness, batch handoff packaging, runner/queue dry-run staging, queue-bundle planning, and emission manifest sequencing.

## Adapter Coverage
- UFC: 1 event(s)
- PFL: 1 event(s)
- ONE: 1 event(s)

## Queue Bundles: 1
## Manifest Entries: 1
## Dispatch Ready: 1
## Dispatch Blocked: 2

## Dispatch Order by Queue Target
- queue_ufc_event_batch: 1 entries
  - manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1 (dispatch_order=1)

## Normalized Events

- **ID:** ufc_300 | **Date:** 2026-04-13 | **Promotion:** UFC | **Venue:** T-Mobile Arena | **Sport:** MMA | **Divisions:** Lightweight, Welterweight | **Source:** UFC_API | **Adapter Status:** ok | **Complete:** True | **Queue Bundle ID:** bundle_queue_ufc_event_batch_1 | **Bundle Position:** 1 | **Bundle Emission Ready:** True | **Manifest ID:** manifest_bundle_queue_ufc_event_batch_1_handoff_ufc_300_UFC_API_v1 | **Manifest Position:** 1 | **Dispatch Order:** 1 | **Dispatch Ready:** True | **Dispatch Blockers:** []
- **ID:** pfl_2026_01 | **Date:** 2026-05-01 | **Promotion:** PFL | **Venue:** unknown | **Sport:** MMA | **Divisions:** Featherweight | **Source:** PFL_FEED | **Adapter Status:** ok | **Complete:** False | **Queue Bundle ID:** None | **Bundle Position:** None | **Bundle Emission Ready:** False | **Manifest ID:** None | **Manifest Position:** None | **Dispatch Order:** None | **Dispatch Ready:** False | **Dispatch Blockers:** ['not bundle emission ready']
  - Missing: venue
  - Blockers: venue
  - Excluded from handoff: not handoff-ready
- **ID:** one_2026_04 | **Date:** unknown | **Promotion:** ONE | **Venue:** Singapore Indoor Stadium | **Sport:** MMA | **Divisions:** None | **Source:** ONE_CHAMPIONSHIP | **Adapter Status:** incomplete | **Complete:** False | **Queue Bundle ID:** None | **Bundle Position:** None | **Bundle Emission Ready:** False | **Manifest ID:** None | **Manifest Position:** None | **Dispatch Order:** None | **Dispatch Ready:** False | **Dispatch Blockers:** ['not bundle emission ready']
  - Missing: date, divisions
  - Blockers: date, divisions
  - Excluded from handoff: not handoff-ready

This file defines the normalization contract, adapter coverage, dependency readiness, batch handoff packaging, runner staging, queue emission dry-run, queue-bundle planning, and emission manifest sequencing format.
