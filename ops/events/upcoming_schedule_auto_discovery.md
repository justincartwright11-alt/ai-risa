# Upcoming Schedule Runner Staging Dry Run

This deterministic output is based on embedded source fixtures, adapter logic, dependency readiness, batch handoff packaging, and runner/queue dry-run staging.

## Adapter Coverage
- UFC: 1 event(s)
- PFL: 1 event(s)
- ONE: 1 event(s)

## Handoff Ready: 1 / 3
## Included in Handoff: 1
## Blocked Events: 2
## Staged for Runner: 1
## Queue Emission Previews: 1

## Handoff Payload IDs
- handoff_ufc_300_UFC_API_v1

## Runner Stage IDs
- runner_stage_handoff_ufc_300_UFC_API_v1

## Normalized Events

- **ID:** ufc_300 | **Date:** 2026-04-13 | **Promotion:** UFC | **Venue:** T-Mobile Arena | **Sport:** MMA | **Divisions:** Lightweight, Welterweight | **Source:** UFC_API | **Adapter Status:** ok | **Complete:** True | **Dependency Status:** ready | **Handoff Ready:** True | **Included in Handoff:** True | **Staged for Runner:** True | **Runner Stage Status:** staged | **Queue Emission Preview:** {'queue_target': 'queue_ufc_event_batch', 'payload_id': 'handoff_ufc_300_UFC_API_v1', 'dry_run_only': True} | **Dry Run Only:** True
- **ID:** pfl_2026_01 | **Date:** 2026-05-01 | **Promotion:** PFL | **Venue:** unknown | **Sport:** MMA | **Divisions:** Featherweight | **Source:** PFL_FEED | **Adapter Status:** ok | **Complete:** False | **Dependency Status:** blocked | **Handoff Ready:** False | **Included in Handoff:** False | **Staged for Runner:** False | **Runner Stage Status:** not_staged | **Queue Emission Preview:** None | **Dry Run Only:** True
  - Missing: venue
  - Blockers: venue
  - Excluded from handoff: not handoff-ready
- **ID:** one_2026_04 | **Date:** unknown | **Promotion:** ONE | **Venue:** Singapore Indoor Stadium | **Sport:** MMA | **Divisions:** None | **Source:** ONE_CHAMPIONSHIP | **Adapter Status:** incomplete | **Complete:** False | **Dependency Status:** blocked | **Handoff Ready:** False | **Included in Handoff:** False | **Staged for Runner:** False | **Runner Stage Status:** not_staged | **Queue Emission Preview:** None | **Dry Run Only:** True
  - Missing: date, divisions
  - Blockers: date, divisions
  - Excluded from handoff: not handoff-ready

This file defines the normalization contract, adapter coverage, dependency readiness, batch handoff packaging, runner staging, and queue emission dry-run format.
