# AI-RISA Paid Pilot Operator Delivery Pack v1

## 1. Paid Pilot Objective
- Controlled manual pilot for AI-RISA Premium Fight Intelligence Report
- Limited customer count (founding cohort)
- Every delivery is manually reviewed by an operator before sending
- No automatic or external API delivery

## 2. Customer Offer
- **Product:** AI-RISA Premium Fight Intelligence Report
- **What the customer receives:**
  - Professionally generated PDF report for requested fight(s)/event(s)
  - 24-page, customer-ready, source-traceable intelligence dossier
  - Manual operator QA before delivery
- **What it is not:**
  - Not a guaranteed pick or betting outcome
  - Not financial advice
  - Not automated betting instruction

## 3. Pricing Test Options
- Single premium report (per fight)
- Multi-fight pack (multiple matchups)
- Full event-card pack (all fights on a card)
- Founding customer discount option (optional)

## 4. Customer Intake Checklist
- Fight/event requested
- Customer type: fan, coach, analyst, bettor, gym, promoter
- Delivery email/contact
- Required deadline
- Special focus requested: tactical, betting-market, coaching, scouting, broadcast

## 5. Operator Workflow
1. Start dashboard on port 5050
2. Button 1: confirm/promote ready fights
3. Button 2: refresh queue
4. Select one/multiple/all-ready fights
5. Generate PDFs
6. Open generated PDFs
7. Perform QA check (see below)
8. Deliver manually to customer
9. Record delivery in daily log

## 6. PDF QA Checklist
- Correct fighters and event
- Correct source map
- 24 pages present
- No stale matchup names
- Open PDF link works
- Report is customer-ready (no placeholders)
- Disclaimer present
- No broken/empty sections
- No obvious visual overlap or rendering errors

## 7. Delivery Script
**Customer message:**
> Your AI-RISA Premium Fight Intelligence Report is attached. This report is for informational and entertainment purposes only. Please review the attached PDF and let us know if you have any questions or require a revision.

**Disclaimer:**
> This report is not financial advice, not a guaranteed outcome, and not an automated betting instruction. All analysis is for informational purposes only.

**Revision/error handling:**
> If you notice any errors, missing pages, or incorrect matchups, reply to this message and we will review and correct your report promptly.

## 8. Refund/Error Policy
- Full refund or free revision for:
  - Wrong matchup delivered
  - Broken or unreadable PDF
  - Missing pages or sections
  - Source issue or data error
  - Delayed delivery (missed deadline)
  - Customer revision request (reasonable)

## 9. Daily Pilot Log Template
| Date       | Customer | Fight/Event | PDFs Generated | Delivered (Y/N) | Issues | Revenue | Notes |
|------------|----------|-------------|----------------|------------------|--------|---------|-------|
| YYYY-MM-DD |          |             |                |                  |        |         |       |

## 10. Pilot GO/NO-GO Rules
- **GO:**
  - Dashboard loads
  - Queue rows appear
  - PDFs generate and open
  - QA passes
- **NO-GO:**
  - Queue fails to load
  - Generated PDF mismatch or error
  - Governance or approval fails
  - Open PDF links fail

## 11. Governance Lock
- Confirmed in app and API responses:
  - delivery_performed: false
  - external_api_delivery_performed: false
  - learning_apply_performed: false
  - calibration_write_performed: false
  - button3_mutation_performed: false
  - Manual delivery only

## 12. Final Verdict
AI-RISA is ready for a controlled paid pilot with manual operator delivery. All governance and QA rules are enforced. No code, queue, or renderer changes are included in this pack.

---

**Validation:**
- `git status --short` (docs/JSON only)
- `git diff --name-status`
- `git diff --stat`

**Commit only:**
- docs/paid_pilot_operator_delivery_pack_v1.md
- ops/release_checks/paid_pilot_operator_delivery_pack_v1/paid_pilot_delivery_pack_summary.json

**Commit message:**
paid-pilot-operator-delivery-pack-v1: create controlled paid-pilot operator delivery pack

**Tag:**
paid-pilot-operator-delivery-pack-v1
