# Resume AI-RISA Internal Build Priority Selection v1

## 1. Purpose
This document resumes AI-RISA internal build priority selection after the repository instruction system and advisory workflow final internal lock.

## 2. Selection Boundary
This is docs-only priority selection.

It does not authorize:

- runtime changes
- test changes
- workflow changes
- customer release
- public publishing
- production launch
- automated delivery
- learning activation
- calibration writes
- GCID writes
- accuracy-ledger writes
- database writes

## 3. Release Boundary
RELEASE_SCOPE_DECISION=INTERNAL_ONLY

CUSTOMER_RELEASE_AUTHORIZED=NO

PUBLIC_PUBLISHING_AUTHORIZED=NO

PRODUCTION_LAUNCH_AUTHORIZED=NO

AUTOMATED_DELIVERY_AUTHORIZED=NO

LEARNING_ACTIVATION_AUTHORIZED=NO

## 4. Current Locked Foundation
Confirm:

- repository instruction system locked
- advisory workflow locked
- default branch aligned to ai-risa-mainline
- manual advisory workflow observation succeeded
- Button 1/2/3 internal readiness audit previously passed
- customer release remains unauthorized

## 5. Candidate Internal Build Priorities
Candidate A -- Button 2 Premium Report Update Versioning Implementation Readiness

- builds from existing design, contract, and review chain
- supports internal report refresh before customer delivery
- keeps customer delivery blocked
- suitable for narrow schema/test-first work

Candidate B -- Button 1 Queue Source Refresh / Source Trust Hardening

- improves fight discovery/source confidence
- must avoid silent queue/database save
- useful but lower immediate value than report versioning if Button 2 refresh chain is already designed

Candidate C -- Button 3 Accuracy Ledger / Controlled Learning Expansion

- high value
- highest governance risk
- must remain preview-only unless separately authorized
- not the first resume slice after workflow governance lock

Candidate D -- Customer Release Gate Design

- commercially important
- premature until Button 2 update/versioning implementation and validation are stronger

## 6. Selection Criteria
Use these criteria:

- highest internal value
- lowest governance risk
- already designed/reviewed
- narrow implementation path
- no customer release
- no learning activation
- no database/ledger mutation
- test-first possible
- supports Button 2 premium report quality

## 7. Selected Priority
Button 2 Premium Report Update Versioning Implementation Readiness

This is the next safest internal build priority.

## 8. Recommended Next Slice
Recommend:

button2_premium_report_update_versioning_fixture_schema_test_design_v1

The next slice should be docs-only or test-design-only first, defining the exact fixture/schema/test target before any runtime implementation.

Do not jump straight to broad implementation.

## 9. Blocked / Deferred Items
Deferred:

- customer release
- public publishing
- production launch
- automated delivery
- learning activation
- Button 3 ledger writes
- GCID writes
- calibration writes
- broad Button 1/2/3 refactors
- workflow expansion

## 10. Priority Decision
NEXT_INTERNAL_BUILD_PRIORITY_SELECTED=BUTTON2_PREMIUM_REPORT_UPDATE_VERSIONING_IMPLEMENTATION_READINESS

## 11. Slice Integrity
DOCS_CHANGED=YES
WORKFLOW_CHANGED=NO
CODE_CHANGED=NO
TEST_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY