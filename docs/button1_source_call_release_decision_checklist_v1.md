# Button 1 Source-Call Release Decision Checklist v1

## Current locked state

- Button 1 source-call work is paused.
- Current checkpoint: 7d70f40.
- Current tag: button1-source-call-pause-and-release-checkpoint-v1.
- Runtime preview remains deny-by-default.
- live_save_allowed remains false.
- No provider execution is approved.
- No network/source call is approved.
- No write path is approved.

## Mandatory operator checklist
Every item must be answered YES before release planning may begin:

1. Is a new docs-only live-call authorization design approved?
2. Is the exact provider limited to ufc_official_events?
3. Does one_fc_official_events remain disabled?
4. Is no more than one provider enabled?
5. Is operator approval modeled separately from source-call authorization?
6. Is source-call authorization modeled separately from provenance?
7. Is provenance modeled separately from save approval?
8. Is save approval modeled separately from Button 2 promotion?
9. Is max_result_count explicitly bounded?
10. Is timeout_seconds explicitly bounded?
11. Is the approved source domain explicitly locked?
12. Is the approved HTTP method explicitly locked?
13. Is the expected response type explicitly locked?
14. Is recursive crawling prohibited?
15. Is unbounded retrieval prohibited?
16. Are token secrets excluded from code, logs, outputs, audit, tests, and proof documents?
17. Are no-write invariants defined?
18. Are provider execution, network calls, and source calls separately audited?
19. Are parser failure, stale feed, unavailable feed, and provenance conflict separately diagnosed?
20. Is a focused test file defined?
21. Is an exact staged-set guard defined?
22. Is a rollback and abort policy defined?
23. Is a read-only runtime-validation gate defined?
24. Is explicit operator approval required before implementation?
25. Are sufficient Copilot credits or an approved additional-usage budget available?

## Automatic decision rule

- Any NO answer means: KEEP PAUSED.
- Any UNKNOWN answer means: KEEP PAUSED.
- Missing evidence means: KEEP PAUSED.
- Only unanimous YES answers permit a new docs-only implementation-readiness planning slice.
- Completing this checklist does not authorize execution.

## Still blocked after checklist completion

- Real token use
- Provider execution
- Network/source calls
- Scraping
- Queue/database writes
- Customer PDF/report generation
- Button 2 promotion
- Learning/calibration writes
- Auto-save
- UI changes
- Provider registry changes

## Required approval record
Include fields for:

- operator name
- review date
- checkpoint reviewed
- tag reviewed
- checklist result
- unresolved blockers
- operator decision
- signature or approval identifier

## Final verdict
BUTTON1_SOURCE_CALL_RELEASE_REQUIRES_UNANIMOUS_OPERATOR_CHECKLIST_APPROVAL
