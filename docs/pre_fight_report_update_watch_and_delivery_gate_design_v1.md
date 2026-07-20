# Pre-Fight Report Update Watch and Delivery Gate Design v1

## 1. Purpose
This module keeps reports current before fight time by checking online and offline evidence, identifying material changes, refreshing internal premium report drafts when appropriate, and preserving a fail-closed delivery gate until the customer and operator explicitly request and approve delivery.

## 2. Release Boundary
- RELEASE_SCOPE_DECISION=INTERNAL_ONLY
- CUSTOMER_RELEASE_AUTHORIZED=NO
- PUBLIC_PUBLISHING_AUTHORIZED=NO
- PRODUCTION_LAUNCH_AUTHORIZED=NO
- AUTOMATED_DELIVERY_AUTHORIZED=NO
- LEARNING_ACTIVATION_AUTHORIZED=NO

## 3. Module Name
Pre-Fight Report Update Watch

## 4. Placement Inside AI-RISA
This module sits behind Advanced Dashboard.

It is not a fourth main dashboard button.

It feeds:

- Button 1 source verification and fight queue status
- Button 2 premium report refresh
- Button 3 later result comparison and accuracy review

## 5. Online Source Watch
The online watch layer should monitor the following update categories before fight time:

- official promotion event pages
- official fighter profile pages
- commission or sanctioning records where available
- official social media posts
- official weigh-in results
- press conference / face-off / open workout footage
- verified media reports
- odds/market snapshots where market layer is permitted
- injury, withdrawal, replacement, venue, ruleset, or bout-order updates
- referee/judging/commission updates where available

Source trust must be scored before report impact is assigned so that low-trust noise does not override verified fight evidence.

## 6. Offline Source Watch
The offline watch layer should monitor the following internal or operator-provided update categories:

- local GCID records
- saved fight queue records
- prior generated reports
- operator notes
- manually uploaded files
- manually pasted fight-week observations
- saved fighter profiles
- camp notes where permitted
- local video notes
- internal research files
- previous Button 3 result history
- War Room notes

## 7. Update Classification
Every detected update must be classified as one of:

- factual correction
- event status update
- fighter identity update
- record/statistical update
- fight-week behavioural observation
- physical appearance observation
- tactical footage cue
- injury/medical claim requiring caution
- market movement
- venue/ruleset/scheduled-round update
- uncertainty increase
- uncertainty reduction
- no material report impact

## 8. Report Impact Levels
Impact levels define how strongly an update changes the internal report state:

- LEVEL 0 — No change
- LEVEL 1 — Minor wording update
- LEVEL 2 — Evidence note update
- LEVEL 3 — Section recalculation required
- LEVEL 4 — Projection recalibration required
- LEVEL 5 — Report hold / delivery blocked

Examples:

- opponent change = LEVEL 5
- official bout cancelled = LEVEL 5
- weigh-in miss = LEVEL 4 or LEVEL 5 depending ruleset
- minor interview quote = LEVEL 1 or LEVEL 2
- verified injury report = LEVEL 4 or LEVEL 5
- market movement without source evidence = LEVEL 2 only unless supported by fight evidence

## 9. Report Versioning
Every refreshed report must record:

- original report ID
- update timestamp
- update source
- update classification
- impact level
- changed sections
- unchanged sections
- operator decision
- new draft version
- delivery status

Use version labels:

- DRAFT_INTERNAL_v1
- DRAFT_INTERNAL_UPDATED_v2
- DRAFT_INTERNAL_UPDATED_v3
- DELIVERY_READY_PENDING_OPERATOR_APPROVAL
- DELIVERED_TO_CUSTOMER

## 10. Delivery Gate
No report may be sent to a customer automatically.

Customer delivery requires:

1. customer request or active order
2. latest source watch completed
3. report freshness check passed
4. operator review
5. operator delivery approval
6. delivery log
7. final PDF hash recorded

## 11. Customer Delivery Statuses
Define the following statuses:

- NOT_FOR_CUSTOMER
- INTERNAL_DRAFT
- WATCH_ACTIVE
- UPDATE_PENDING_REVIEW
- REPORT_HOLD
- DELIVERY_READY_PENDING_OPERATOR_APPROVAL
- CUSTOMER_DELIVERY_APPROVED
- DELIVERED
- DELIVERY_REVOKED_OR_SUPERSEDED

## 12. Fight-Week Intelligence / PECI Connection
Behavioural, weigh-in, face-off, and fight-week observations may feed PECI only when they have source, timestamp, context, confidence, baseline comparison, and operator notes.

Do not infer private emotion as fact.

## 13. Button 1 Integration
Button 1 must:

- discover/update fight records
- flag event changes
- update readiness ranking
- mark source trust changes
- block report generation if identity/event/ruleset is unresolved

## 14. Button 2 Integration
Button 2 must:

- regenerate or refresh the premium report draft when material updates occur
- show changed sections
- preserve previous draft version
- update source map
- update uncertainty notes
- hold delivery until operator approval

## 15. Button 3 Integration
Button 3 must:

- later compare the final delivered or final internal pre-fight report against official results
- record which report version was active at fight start
- prevent learning from obsolete drafts unless explicitly reviewed
- keep controlled learning gated

## 16. Automation Boundary
Allowed:

- scheduled online checks
- local/offline evidence scans
- change detection
- draft refresh
- report hold flags
- operator notification

Not allowed without separate authority:

- customer sending
- public publishing
- production launch
- permanent learning update
- uncontrolled database mutation
- hidden report replacement
- changing release scope

## 17. Fail-Closed Rules
AI-RISA must block delivery when:

- fighter identity is unresolved
- event status is uncertain
- opponent changes
- official source conflicts remain unresolved
- report is stale
- material fight-week update is pending review
- source trust falls below threshold
- operator approval is missing

## 18. Acceptance Criteria
The design is accepted when it defines:

- online source watch
- offline source watch
- report update classification
- impact levels
- report versioning
- customer delivery gate
- Button 1 integration
- Button 2 integration
- Button 3 integration
- fail-closed rules
- internal-only status

## 19. Slice Integrity
- DOCS_CHANGED=YES
- CODE_CHANGED=NO
- PDF_CHANGED=NO
- DATA_CHANGED=NO
- CUSTOMER_RELEASE_AUTHORIZED=NO
- RELEASE_SCOPE_DECISION=INTERNAL_ONLY