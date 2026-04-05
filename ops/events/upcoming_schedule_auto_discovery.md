# Upcoming Schedule Dependency Readiness

This deterministic output is based on embedded source fixtures, adapter logic, and dependency readiness assessment.

## Adapter Coverage
- UFC: 1 event(s)
- PFL: 1 event(s)
- ONE: 1 event(s)

## Handoff Readiness: 1 ready / 3 total
## Blocked Events: 2

## Normalized Events

- **ID:** ufc_300 | **Date:** 2026-04-13 | **Promotion:** UFC | **Venue:** T-Mobile Arena | **Sport:** MMA | **Divisions:** Lightweight, Welterweight | **Source:** UFC_API | **Adapter Status:** ok | **Complete:** True | **Dependency Status:** ready | **Handoff Ready:** True
- **ID:** pfl_2026_01 | **Date:** 2026-05-01 | **Promotion:** PFL | **Venue:** unknown | **Sport:** MMA | **Divisions:** Featherweight | **Source:** PFL_FEED | **Adapter Status:** ok | **Complete:** False | **Dependency Status:** blocked | **Handoff Ready:** False
  - Missing: venue
  - Blockers: venue
- **ID:** one_2026_04 | **Date:** unknown | **Promotion:** ONE | **Venue:** Singapore Indoor Stadium | **Sport:** MMA | **Divisions:** None | **Source:** ONE_CHAMPIONSHIP | **Adapter Status:** incomplete | **Complete:** False | **Dependency Status:** blocked | **Handoff Ready:** False
  - Missing: date, divisions
  - Blockers: date, divisions

This file defines the normalization contract, adapter coverage, dependency readiness, and batch handoff format.
