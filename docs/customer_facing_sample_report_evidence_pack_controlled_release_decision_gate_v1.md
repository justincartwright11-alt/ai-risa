# Customer Facing Sample Report Evidence Pack Controlled Release Decision Gate v1

## 1. Purpose
Define a docs-only controlled-release decision gate for the customer-facing sample report evidence pack. This slice creates the decision gate only and does not authorize release.

## 2. Current locked status
- PDF_DRAFT_REVIEW_DECISION=APPROVED_FOR_INTERNAL_REVIEW_ONLY
- Customer release: NO
- Public publishing: NO
- Production launch: NO
- Automated delivery: NO
- Learning activation: NO

## 3. Reviewed PDF artifact
- reports/ai_risa_controlled_validation_evidence_pack_batch_2_minimum_proof_customer_facing_draft_v1.pdf

## 4. Locked product identifiers
SKU:
- AI-RISA-EVIDENCE-PACK-BATCH2-MIN-PROOF-V1

Product name:
- AI-RISA Controlled Validation Evidence Pack — Batch 2 Minimum Proof

Price candidate:
- AUD $29 introductory internal-approved customer-facing price candidate

## 5. Locked review decision
PDF_DRAFT_REVIEW_DECISION=APPROVED_FOR_INTERNAL_REVIEW_ONLY

## 6. Controlled-release gate objective
Define the explicit decisions required before a later limited controlled customer release can be authorized. This slice creates the decision gate only and does not authorize release.

## 7. Required operator decisions before release
- approve exact PDF artifact
- approve exact SKU
- approve exact product name
- approve exact price
- approve buyer-facing claims
- approve disclaimer and FAQ language
- approve manual payment path
- approve manual delivery path
- approve refund/support rules
- approve access-control rules
- approve audit/evidence requirements
- approve rollback/recall rules
- approve release scope and recipient class
- approve final release date/time window

## 8. Required release-scope decision
Allowed decision options:
- INTERNAL_ONLY
- LIMITED_CONTROLLED_CUSTOMER_PILOT
- PUBLIC_RELEASE
- PRODUCTION_LAUNCH

## 9. Required payment decision
- Confirm manual operator-approved payment path only until later automation authorization.
- Confirm payment evidence and audit requirements are active.
- Confirm chargeback/dispute handling is approved before any future release decision.

## 10. Required delivery/access-control decision
- Confirm manual operator-approved delivery path only until later automation authorization.
- Confirm access-controlled delivery channels only.
- Confirm no open public download link is permitted.

## 11. Required refund/support decision
- Confirm refund rule set is approved before any future customer release decision.
- Confirm support channels, response windows, and escalation boundaries are approved.
- Confirm support does not provide betting advice or guarantee claims.

## 12. Required legal/disclaimer decision
- Confirm disclaimer and FAQ lock language remains unchanged.
- Confirm prohibited claims remain absent in customer-facing materials.
- Confirm legal review completion is required before any external release authorization.

## 13. Required risk and rollback decision
- Confirm rollback/recall trigger conditions are defined before any release authorization.
- Confirm high-risk issue escalation path is approved.
- Confirm release-window suspension authority is assigned.

## 14. Prohibited release modes
- no public publishing
- no production launch
- no automated delivery
- no automated learning activation
- no open public download link
- no redistribution permission
- no claim of guaranteed accuracy
- no betting-advice positioning
- no proof-across-all-combat-sports claim

## 15. Decision matrix
- Internal review: ALLOWED
- Limited controlled customer pilot: NOT AUTHORIZED IN THIS SLICE
- Public release: NOT AUTHORIZED
- Production launch: NOT AUTHORIZED
- Automated delivery: NOT AUTHORIZED
- Learning activation: NOT AUTHORIZED

## 16. Gate result
CONTROLLED_RELEASE_DECISION=HOLD_NOT_AUTHORIZED

The controlled-release decision gate is created, but release remains on HOLD until a later explicit operator release-decision record is created.

## 17. Recommended next slice
customer-facing-sample-report-evidence-pack-operator-release-decision-record-v1

## 18. Stop condition
Stop after this decision-gate document. Do not modify code, data, or PDFs; do not regenerate artifacts; do not run fights or runtime tests; and do not authorize customer release, public publishing, production launch, automated delivery, or learning activation in this slice.