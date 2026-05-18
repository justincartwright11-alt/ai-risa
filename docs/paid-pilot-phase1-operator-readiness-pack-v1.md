# Paid-Pilot Phase 1 Operator Readiness Pack v1

**Document Type:** Operational Readiness Pack (Docs/Ops/Business Only)  
**Date:** 2026-05-18  
**Status:** Operator Readiness Documentation  
**Locked Checkpoint:** commercial-release-readiness-index-v1 (commit b5b9abe)  
**Product Scope:** Button 2 Premium PDF Generation + Phase 7 Controlled Delivery  
**Pilot Target:** 3–5 initial paying customers, 2–4 week pilot window

---

## Executive Summary

This pack prepares operators and customer-facing teams to launch and manage the AI-RISA paid-pilot Phase 1. It covers operator procedures, customer onboarding, demo scripts, delivery rules, support expectations, and go/no-go checklist. **No code changes are included. Implementation remains frozen.**

---

## 1. Pilot Operator Runbook

### 1.1 Daily Operator Workflow

**Typical daily sequence:**

1. **Morning: Check pilot customer queue**
   - Login to AI-RISA dashboard
   - Navigate to Button 1 queue view
   - Review manual fight queue entries from overnight (if any)
   - Verify queue status and report readiness

2. **Mid-morning: Process fight queue**
   - Select 1–3 fights from queue ready for PDF generation
   - Click "Generate Premium Reports" (Button 2 main dashboard button)
   - Approve PDF generation (no external data fetch, no delivery)
   - Verify PDFs generated successfully
   - Store file paths for delivery staging

3. **Pre-delivery: Controlled delivery approval**
   - Navigate to controlled delivery panel
   - Review preflight eligibility check (/api/button2/controlled-delivery/preview)
   - Verify report status is "customer_ready"
   - Verify channel is "manual_export" (current Phase 1 mode)
   - **If preflight PASS:** Review denial reasons, confirm they are all false/safe
   - **If preflight FAIL:** Check dashboard for specific denial reason; investigate before proceeding

4. **Delivery: Execute controlled action**
   - Click "Approve & Deliver" (or equivalent operator action button)
   - System executes controlled delivery action endpoint
   - Audit record, proof_of_delivery_record, and delivery_receipt_record generated
   - Evidence displays in audit panel with cross-referenced IDs
   - Operator records delivery ID for compliance tracking

5. **Post-delivery: Compliance logging**
   - Screenshot or export audit/proof evidence (if required by SLA)
   - Verify evidence record IDs match
   - Log delivery in customer communication system
   - Send customer notification with delivery confirmation

6. **End-of-day: Shift close**
   - Review all deliveries completed
   - Check for any denial/error messages in dashboard
   - Export compliance audit if required
   - Handoff to next shift or close day

### 1.2 Controlled Delivery Approval Workflow

**Before Approving:**

- [ ] Report is marked "customer_ready" (not draft, not internal)
- [ ] Preflight check returned PASS (200)
- [ ] All preflight denial reasons are FALSE (no actual blockers)
- [ ] Channel is "manual_export" (no email_scaffold, no api_scaffold)
- [ ] Operator confirms intentional delivery to this customer
- [ ] Customer account is active and paid

**During Approval:**

- [ ] Click "Approve & Deliver" button in controlled delivery panel
- [ ] System returns 200 OK with evidence objects
- [ ] Audit record displays with operation_id
- [ ] Proof_of_delivery_record displays with proof_id
- [ ] Receipt record displays with receipt_id
- [ ] Dashboard shows all IDs linked (cross-referenced)

**After Approval:**

- [ ] Verify operation_id, proof_id, receipt_id are all populated
- [ ] Log delivery ID in customer tracking system
- [ ] Notify customer of delivery
- [ ] Retain audit evidence for compliance

### 1.3 Denial / Error Recovery

**If preflight check returns 400 (DENIED):**

1. Dashboard displays explicit denial reason (e.g., "draft status", "internal marking")
2. **DO NOT OVERRIDE.** Denial is hard block.
3. Investigate reason:
   - Is report status actually draft? → Regenerate as customer_ready
   - Is report marked internal? → Check report metadata and remove internal flag
   - Is channel not manual_export? → Verify only manual_export channel is active
4. Correct the issue
5. Re-run preflight check
6. If preflight now PASS, proceed with approval

**If preflight check returns 500 (ERROR):**

1. Dashboard displays error message
2. **DO NOT RETRY IMMEDIATELY.** Wait 5 minutes.
3. Check system status dashboard
4. If error persists, escalate to technical support (see Support Escalation section)

### 1.4 Safety Boundaries Operators MUST Respect

**MANDATORY:**
- [ ] Operator approval is required before every delivery
- [ ] Draft/internal reports must NOT be delivered to customers
- [ ] Denial reasons are hard stops; do NOT bypass or override
- [ ] Only manual_export channel is active (no email sends, no external API calls)
- [ ] Evidence records must be retained for compliance audit

**PROHIBITED:**
- ❌ Do NOT send email directly from AI-RISA (email_scaffold is non-operational)
- ❌ Do NOT use external delivery APIs (api_scaffold is non-operational)
- ❌ Do NOT bypass preflight check
- ❌ Do NOT override denial messages
- ❌ Do NOT deliver draft/internal reports

---

## 2. Customer Onboarding Checklist

### 2.1 Pre-Pilot Kickoff (T-5 days before first delivery)

**Customer Account Setup:**
- [ ] Customer account created in AI-RISA
- [ ] Login credentials sent (secure channel)
- [ ] API key generated (if customer API integration planned)
- [ ] Compliance/NDA signed and filed

**Customer Data Configuration:**
- [ ] Fighter roster provided by customer (if needed for context)
- [ ] Event calendar uploaded
- [ ] Report branding/custom sections configured
- [ ] Delivery email list collected

**Operator Training:**
- [ ] Customer assigned a dedicated pilot operator
- [ ] Operator trained on Button 2 queue entry and PDF generation
- [ ] Operator trained on controlled delivery approval workflow
- [ ] Operator trained on support escalation procedure

**First-Run Validation:**
- [ ] Generate test PDF for one of customer's recent fights
- [ ] Customer reviews test PDF for format, content, accuracy
- [ ] Customer provides feedback on sections, depth, tone
- [ ] Operator and customer agree on PDF customization (if any)

### 2.2 Pilot Launch Week (T-0 to T+7 days)

**Week 1 Setup:**
- [ ] Customer receives first batch of fight queue for upcoming week (3–5 fights)
- [ ] Customer approves which fights to generate PDFs for
- [ ] Operator generates PDFs for approved fights
- [ ] PDFs delivered to customer via secure link or direct download

**Customer Feedback Collection:**
- [ ] Daily standup call or async chat with customer
- [ ] Customer provides feedback on:
  - PDF quality and accuracy
  - Sections that are most/least valuable
  - Delivery turnaround time
  - Any formatting issues

**Operator Feedback:**
- [ ] Operator logs workflow issues (if any)
- [ ] Operator reports approval workflow clarity
- [ ] Operator reports any system errors or edge cases

### 2.3 Pilot Stabilization (Week 2–4)

**Ongoing Operations:**
- [ ] Operator processes fight queues as they arrive
- [ ] Customer reviews and approves PDFs on a rolling basis
- [ ] Delivery approval workflow becomes routine

**Mid-Pilot Check-in (Week 2):**
- [ ] Customer satisfaction survey
- [ ] Operator workload assessment
- [ ] Any critical issues or feature requests?

**Late Pilot Check-in (Week 4):**
- [ ] Cumulative metrics (# of fights, # of PDFs delivered, # of customers)
- [ ] Customer NPS / satisfaction score
- [ ] Operator efficiency (# of deliveries per hour, error rate)
- [ ] Decision: Continue to Phase 2 or adjust scope?

---

## 3. Demo Script

### 3.1 Demo Opening (1 minute)

**Narrator:**
> "Welcome to AI-RISA Premium Report Factory. We're going to walk through a live workflow that an operator uses every day to generate and deliver premium fight intelligence reports to paying customers.
>
> Here's what we're building: a simple, auditable system that finds upcoming fights, generates detailed PDF reports about those fights, and delivers them with full approval gates and evidence trails. Everything stays under operator control. No uncontrolled automation, no silent background delivery, just clear, visible, governed workflows.
>
> Let's start with the main dashboard."

### 3.2 Demo Flow: Main Dashboard (1 minute)

**Screen Share:** Main AI-RISA dashboard

**Narrator:**
> "This is the main dashboard. Three buttons. That's it. Everything else is behind 'Advanced Dashboard' for internal tools.
>
> Button 1 is 'Find & Build Fight Queue' — that's how operators discover and queue upcoming fights. Button 2 is 'Generate Premium PDF Reports' — that's the core product. And Button 3 is 'Find Results & Improve Accuracy' — that's future work for now.
>
> For this pilot, we're focusing on Button 2. Let me show you a queued fight."

### 3.3 Demo Flow: Button 2 PDF Generation (2 minutes)

**Screen Share:** Button 2 selection screen (pre-loaded with sample fight)

**Narrator:**
> "Let's say a customer has a fight they want intelligence on: Fighter A vs Fighter B, upcoming next week. The operator has already entered this into the fight queue.
>
> The operator selects the fight from the queue and clicks 'Generate Premium Report.' The system collects data on both fighters — their records, style, injury history, betting odds, event context — and generates a beautiful, 26-page professional PDF report. All sourced. All cited. Ready to send to paying customers.
>
> Let me show you a sample PDF that was generated this morning."

**Screen Share:** Sample 26-page premium PDF in browser

**Narrator (while scrolling PDF):**
> "Page 1 is an executive summary of the matchup and our prediction.
> Pages 2–8 are deep fighter profiles — record, win loss, injury risk, style strengths, weaknesses.
> Pages 9–14 are matchup analysis — how does Fighter A's style match up against Fighter B? What are the tactical edges?
> Pages 15–20 are event context — venue, weather, crowd, betting odds.
> Pages 21–24 are scenario trees — what happens if Fighter A wins early? What if it goes to the judges?
> Pages 25–26 are a source audit trail — every claim is cited to a specific source, every chart is backed by data.
>
> This is what we're selling. It's premium. It's credible. It's worth money."

### 3.4 Demo Flow: Controlled Delivery Approval (2 minutes)

**Screen Share:** Dashboard controlled delivery panel

**Narrator:**
> "Now, the operator has the PDF ready to send. But here's where governance comes in.
>
> Before the operator can deliver to a customer, the system runs a preflight eligibility check. It asks: Is this report really customer-ready? Is it marked as draft or internal? Is the delivery channel correct? Is the operator actually approved to send it?
>
> The dashboard shows the preflight check results. All green. No blockers. This report is safe to send."

**Screen Share:** Preflight results showing all PASS

**Narrator:**
> "The operator reviews the preflight results. Everything looks good. Now the operator clicks 'Approve & Deliver.' The system executes the delivery action."

**Click:** "Approve & Deliver" button

**Screen Share:** Evidence panel populates with audit, proof, receipt records

**Narrator:**
> "The system returns evidence records. An audit record that logs what happened. A proof_of_delivery_record that confirms the report was sent. A delivery_receipt_record that the customer acknowledges receipt. All with cross-referenced IDs so we can trace every delivery through the entire chain.
>
> This is what governed delivery looks like. Clear. Auditable. Compliant."

### 3.5 Demo Closing (1 minute)

**Narrator:**
> "So here's what makes AI-RISA different:
>
> First, the product is premium. 26 pages of deep intelligence, sourced and cited. Customers will pay for this.
>
> Second, it's governed. Operators approve every delivery. Drafts can't escape. Internal work stays internal. Everything is audited. There's a clear trail for compliance.
>
> Third, it's simple for the operator to use. No software engineering. No databases. No APIs. Just a clean workflow: queue fights, generate reports, approve delivery, retain evidence. Any operator can run this.
>
> We're launching paid-pilot Phase 1 with 3–5 initial customers next month. Button 2 is locked and ready. Phase 7 controlled delivery governance is locked and tested. We've got 99 regression tests passing and 10 smoke checks passing. The foundation is solid.
>
> Questions?"

### 3.6 Sample Q&A

**Q: What if the operator wants to bypass approval and send a draft report?**  
A: They can't. The preflight check will reject it. Denial is a hard block. The system won't execute the delivery. Governance is not optional.

**Q: What happens to Button 1 (queue discovery) and Button 3 (result comparison)?**  
A: They're Phase 2 and Phase 8 work. For Phase 1 paid-pilot, operators will manually enter fights into the queue. That's not a blocker. We get customers paying for Button 2 (PDF generation), then we add automation on top.

**Q: How long does PDF generation take?**  
A: About 30–60 seconds per fight. The operator queues the fight in the morning, clicks "Generate," and has a finished PDF ready by mid-day.

**Q: What about learning and improving accuracy over time?**  
A: That's Button 3, Phase 8 work. Right now we're focused on delivering premium reports on time, with governance. Learning comes next.

**Q: Is there a fallback if the system fails?**  
A: Yes. If a delivery approval fails, the operator can escalate to technical support. We provide a support escalation path (see section below).

---

## 4. Delivery Rules for Paid-Pilot Phase 1

### 4.1 What IS Included in Phase 1

**Allowed Deliveries:**
- ✅ Premium PDF reports generated from customer-queued fights
- ✅ Manual queue entry by operator (no auto-discovery yet)
- ✅ Controlled delivery approval workflow (operator-initiated)
- ✅ Governed delivery to customer (evidence trail retained)
- ✅ Manual download of PDF by customer (secure link)

**Allowed Channels:**
- ✅ manual_export: Operator exports PDF and sends via secure channel (email link, secure download portal, etc.)
- ⚠️ email_scaffold: Placeholder (not active in Phase 1; no real email send)
- ⚠️ api_scaffold: Placeholder (not active in Phase 1; no external API call)

**Allowed Customization:**
- ✅ Customer branding on PDF (logo, watermark)
- ✅ Custom section ordering (if requested, subject to technical review)
- ✅ Report tone adjustments (conservative vs. aggressive predictions)

### 4.2 What IS NOT Included in Phase 1

**Prohibited Features:**
- ❌ Automatic fight discovery (Button 1 auto-search not built yet)
- ❌ Result matching and learning (Button 3 not built yet)
- ❌ Email delivery (email_scaffold is placeholder, no actual send)
- ❌ API-based delivery (api_scaffold is placeholder, no external call)
- ❌ Batch bulk operations (single-fight-at-a-time only)
- ❌ Customer self-service portal (operator-mediated delivery only)
- ❌ Real-time accuracy metrics (Button 3 learning deferred)

### 4.3 Delivery SLA and Expectations

**Report Generation SLA:**
- Target: 30–60 seconds per fight
- SLA: 2-hour max turnaround for report generation (if queue backlog)

**Delivery Approval SLA:**
- Target: 5 minutes from operator request
- SLA: 15-minute max (if system delay)

**Customer Delivery SLA:**
- Target: Same-day delivery to customer (if approved by EOD)
- SLA: Next-business-day delivery guaranteed

**Availability:**
- Hours: Business hours only (8 AM–6 PM ET, weekdays)
- Support: Email during business hours; next-business-day response

---

## 5. Support and SLA Expectations

### 5.1 Support Channels

**Email Support:**
- pilot-support@ai-risa.internal
- Response time: Next business hour during business hours
- Response time: Next business day if submitted after hours

**Escalation Support:**
- pilot-escalation@ai-risa.internal
- Used for: Critical system failures, delivery approval errors
- Response time: Within 30 minutes during business hours

**Emergency Support (if needed):**
- pilot-emergency@ai-risa.internal (for critical production issues)
- Response time: Within 5 minutes
- Used sparingly; coordinate with operations team first

### 5.2 Support Categories

**Category: PDF Generation Quality**
- Issue: Generated PDF is missing sections, has incorrect data, or formatting looks wrong
- Owner: Product team
- Response time: Next business hour
- Mitigation: Provide sample fight data; review against expectations

**Category: Delivery Approval Denied**
- Issue: Preflight check returns 400 DENIED; operator cannot approve delivery
- Owner: Engineering team
- Response time: Within 2 hours
- Mitigation: Provide dashboard screenshots; check report metadata

**Category: Account / Permissions**
- Issue: Customer cannot login, operator permissions incorrect
- Owner: Operations team
- Response time: Next business hour
- Mitigation: Reset credentials; re-configure permissions

**Category: Compliance / Audit**
- Issue: Need to export audit evidence, verify delivery trail
- Owner: Compliance team
- Response time: Next business day
- Mitigation: Provide operation_id; search audit database

### 5.3 SLA Guardrails

**Guaranteed:**
- ✅ Preflight check is never wrong (all denials are actual blockers)
- ✅ Operator approval always succeeds if preflight is PASS
- ✅ Evidence records are always retained and accessible
- ✅ Audit trail is immutable (for compliance)

**NOT Guaranteed (Phase 1):**
- ❌ Automatic fight discovery (Button 1 future work)
- ❌ Learning/accuracy improvement (Button 3 future work)
- ❌ 24/7 support (business hours only)
- ❌ Sub-5-minute response time (best effort during hours)

---

## 6. Legal and Compliance Checklist Placeholders

### 6.1 Legal Checklist

**Items to be completed by Legal team (separate process):**

- [ ] **Customer NDA:** Standard NDA signed by pilot customer before account creation
  - Placeholder: Use template from legal/templates/pilot-nda-standard-v1.docx
  - Owner: Legal team
  - Due: Before customer onboarding

- [ ] **Data Processing Agreement (DPA):** Comply with GDPR/CCPA if customer or data subjects in EU/CA
  - Placeholder: Legal to review AI-RISA data handling against customer jurisdiction requirements
  - Owner: Legal + Privacy team
  - Due: Before customer onboarding

- [ ] **Liability Waiver:** Customer assumes risk for accuracy of predictions
  - Placeholder: Legal to draft "AI-RISA predictions are probabilistic; not guaranteed"
  - Owner: Legal team
  - Due: Before customer onboarding

- [ ] **Confidentiality Clause:** AI-RISA methodology stays confidential; customer data stays confidential
  - Placeholder: Include in NDA
  - Owner: Legal team
  - Due: Before customer onboarding

- [ ] **Support SLA:** Formalize support hours, response times, uptime guarantees
  - Placeholder: See Support section above; Legal to review and formalize
  - Owner: Legal + Operations
  - Due: Before pilot launch

### 6.2 Compliance Checklist

**Items to be completed by Compliance team:**

- [ ] **Audit Trail:** Verify all deliveries are logged, traceable, and immutable
  - Requirement: operation_id, proof_id, receipt_id must be retained for 2 years
  - Owner: Engineering + Compliance
  - Verification: Check ops/release_checks/ evidence logs

- [ ] **Report Classification:** Verify reports are marked "customer_ready" before delivery
  - Requirement: Draft/internal reports must NOT be delivered
  - Owner: Operations + Compliance
  - Verification: Audit dashboard preflight checks

- [ ] **Data Retention:** Define how long customer PDFs and metadata are retained
  - Placeholder: Propose 2-year retention for audit; 90-day deletion for old PDFs
  - Owner: Compliance + Privacy
  - Due: Before pilot launch

- [ ] **Security Review:** Verify PDF files are not accessible to unauthorized users
  - Requirement: Secure download links expire after 7 days; PDFs not stored in shared folders
  - Owner: Security + Operations
  - Due: Before pilot launch

- [ ] **Privacy Review:** Verify no customer data is used for training without consent
  - Requirement: AI-RISA does NOT use pilot data for learning (Button 3 deferred)
  - Owner: Privacy + Engineering
  - Due: Before pilot launch

### 6.3 Business Checklist

**Items to be completed by Business/Commercial team:**

- [ ] **Pilot Customer Contracts:** Signed SOW (Statement of Work) with each pilot customer
  - Terms: Pricing, term length (2–4 weeks), feature set (Button 2 only), support
  - Owner: Business team
  - Due: Before customer onboarding

- [ ] **Pilot Pricing:** Define pilot customer pricing (discount, free, or standard rate)
  - Placeholder: Recommend 50% discount for Phase 1 pilot to incentivize feedback
  - Owner: Business + Finance
  - Due: Before pilot launch

- [ ] **Success Metrics:** Define KPIs to measure pilot success
  - Placeholder: Customer NPS ≥ 7/10, operator efficiency ≥ 5 deliveries/hour, zero critical bugs
  - Owner: Business + Product
  - Due: Before pilot launch

- [ ] **Feedback Process:** Formal process for collecting and acting on customer feedback
  - Placeholder: Weekly customer survey + bi-weekly sync calls
  - Owner: Product + Customer Success
  - Due: Before pilot launch

---

## 7. What IS Included / Excluded in Phase 1

### 7.1 Detailed Inclusion Matrix

| Feature | Included | Status | Notes |
|---------|----------|--------|-------|
| **Core Product** | | | |
| Button 2 PDF generation | ✅ YES | Locked/Ready | 26-page v29 composition, Phase 5 complete |
| Fighter profiles | ✅ YES | Locked/Ready | Record, style, injury risk analysis |
| Matchup analysis | ✅ YES | Locked/Ready | Tactical edges, prediction, confidence |
| Event context | ✅ YES | Locked/Ready | Venue, weather, betting odds |
| Scenario trees | ✅ YES | Locked/Ready | Win/loss/decision paths |
| Source citations | ✅ YES | Locked/Ready | Full audit trail of sources |
| Custom branding | ✅ YES | Locked/Ready | Customer logo, watermark |
| **Discovery** | | | |
| Manual queue entry | ✅ YES | Phase 2 Complete | Operator paste/upload |
| Auto web discovery | ❌ NO | Phase 2 Blocked | Deferred to Phase 2 |
| Ranking/readiness | ❌ NO | Phase 2 Blocked | Deferred to Phase 2 |
| **Delivery** | | | |
| Operator approval gates | ✅ YES | Phase 7 Locked | Preflight + action approval |
| Draft/internal blocking | ✅ YES | Phase 7 Locked | Hard stop for draft reports |
| Manual export | ✅ YES | Phase 7 Locked | Operator exports PDF, sends securely |
| Email delivery | ❌ NO | Placeholder | email_scaffold not active; no real send |
| API delivery | ❌ NO | Placeholder | api_scaffold not active; no external call |
| **Evidence/Audit** | | | |
| Audit record | ✅ YES | Phase 7 Locked | Logs operation_id, metadata |
| Proof of delivery | ✅ YES | Phase 7 Locked | Confirms proof_id, cross-reference |
| Receipt record | ✅ YES | Phase 7 Locked | Customer acknowledge, receipt_id |
| Evidence traceability | ✅ YES | Phase 7 Locked | All IDs linked and searchable |
| **Learning/Accuracy** | | | |
| Result matching | ❌ NO | Phase 8 Blocked | Deferred to Phase 8 |
| Accuracy metrics | ❌ NO | Phase 8 Blocked | Deferred to Phase 8 |
| Learning updates | ❌ NO | Phase 8 Blocked | Deferred to Phase 8 |
| Calibration | ❌ NO | Phase 8 Blocked | Deferred to Phase 8 |
| **Support** | | | |
| Email support | ✅ YES | Ready | Business hours, next-hour response |
| Escalation support | ✅ YES | Ready | Critical issues, 30-min response |
| Audit trail export | ✅ YES | Ready | Compliance team can export evidence |
| **Portal/UX** | | | |
| Operator dashboard | ✅ YES | Phase 7 Locked | Main 3-button, advanced tools |
| Customer self-service | ❌ NO | Future | Deferred to Phase 2+ |
| Mobile app | ❌ NO | Future | Deferred to future phases |
| Bulk operations | ❌ NO | Future | Single-fight-at-a-time only |

### 7.2 Exclusions with Reasons

**Why Button 1 Auto-Discovery is Excluded:**
- Not built yet (design complete, implementation not started)
- Manual queue entry is sufficient for Phase 1 pilot
- Auto-discovery can be added in Phase 2 without changing delivery governance

**Why Button 3 Learning is Excluded:**
- Not built yet (design complete, implementation not started)
- Phase 1 pilot is about PDF generation and delivery governance, not learning
- Learning requires result matching and comparison logic (Phase 8+)
- Adding learning would expand scope and risk Phase 1 timeline

**Why Email Delivery is Not Active:**
- Requires email infrastructure (mail server, credentials, compliance)
- Phase 1 uses manual_export (operator controls delivery)
- Can be activated in Phase 2 if pilot customers request it

**Why API Delivery is Not Active:**
- Requires customer API integration (development work)
- Phase 1 uses manual_export (operator downloads and delivers manually)
- Can be activated in Phase 2 if pilot customers have API infrastructure

---

## 8. Go/No-Go Checklist

### 8.1 Pre-Launch Technical Checklist (Engineering/Ops)

**Code & Tests:**
- [ ] Phase 7 regression: 99/99 passing ✅ (verified in Phase 7 lock)
- [ ] Phase 7 smoke: 10/10 passing ✅ (verified in Phase 7 lock)
- [ ] Button 2 Phase 5: 221+ tests passing ✅ (verified in Phase 5 lock)
- [ ] No known critical bugs in Button 2 PDF generation
- [ ] No known critical bugs in Phase 7 delivery governance
- [ ] All evidence records (audit, proof, receipt) generate correctly
- [ ] Dashboard evidence display is visible and correct

**Deployment & Infrastructure:**
- [ ] Pilot database provisioned and backed up
- [ ] Customer accounts created and credentials distributed
- [ ] API keys generated (if customer integration needed)
- [ ] Secure download links configured (7-day expiry)
- [ ] Audit logging enabled and verified
- [ ] Backup and disaster recovery tested

**Documentation:**
- [ ] Operator runbook completed and tested
- [ ] Customer onboarding checklist completed
- [ ] Demo script tested with stakeholders
- [ ] Support escalation paths defined
- [ ] SLA expectations documented

**Safety:**
- [ ] Preflight check verified for all scenarios (PASS and DENY)
- [ ] Draft/internal blocking verified (cannot be overridden)
- [ ] manual_export channel verified (only active channel)
- [ ] Evidence retention verified (immutable for 2 years)
- [ ] No uncontrolled delivery paths exist

**Sign-off:**
- [ ] Engineering team: Ready ☐
- [ ] Ops team: Ready ☐
- [ ] Compliance team: Ready ☐

### 8.2 Pre-Launch Business Checklist (Commercial)

**Customer & Contracts:**
- [ ] Pilot customer 1: Contract signed, account created, onboarding scheduled
- [ ] Pilot customer 2: Contract signed, account created, onboarding scheduled
- [ ] Pilot customer 3: Contract signed, account created, onboarding scheduled
- [ ] (Pilot customers 4–5: Optional, based on resource availability)

**Pricing & Revenue:**
- [ ] Pilot pricing confirmed (recommend 50% discount for feedback)
- [ ] Invoicing configured (payment terms defined)
- [ ] Revenue recognition policy aligned with Finance

**Success Metrics:**
- [ ] Pilot success KPIs defined (NPS, efficiency, bug-free target)
- [ ] Weekly customer feedback process in place
- [ ] Bi-weekly pilot retrospective scheduled

**Go/No-Go Decision:**
- [ ] Business team: Ready ☐
- [ ] Product team: Ready ☐
- [ ] Finance team: Ready ☐

### 8.3 Pre-Launch Compliance Checklist (Legal/Compliance)

**Legal:**
- [ ] Customer NDA signed by all pilot customers
- [ ] Liability waiver in customer agreement
- [ ] Confidentiality clauses reviewed
- [ ] Support SLA formally documented

**Compliance:**
- [ ] Data retention policy defined (2-year audit trail minimum)
- [ ] Data deletion process defined (90-day retention for PDFs, then delete)
- [ ] Security review completed (download links, file access)
- [ ] Privacy review completed (no training data leakage)

**Regulatory:**
- [ ] GDPR/CCPA review completed (if customer in EU/CA)
- [ ] Data processing agreement signed (if required)
- [ ] Audit trail logging verified for compliance

**Sign-off:**
- [ ] Legal team: Approved ☐
- [ ] Compliance team: Approved ☐

### 8.4 Final Go/No-Go Decision

**GO Decision Criteria (All Must Pass):**
- ✅ All technical tests passing (99/99, 10/10, 221+)
- ✅ All pilot customers contracts signed
- ✅ All legal/compliance approvals obtained
- ✅ Operator runbook and training completed
- ✅ Support infrastructure in place
- ✅ No critical bugs or safety concerns
- ✅ Preflight/denial gates verified and tested

**NO-GO Decision Criteria (Any May Block):**
- ❌ Regression/smoke tests failing
- ❌ Critical bug found in Phase 7 delivery
- ❌ Pilot customer contract not signed
- ❌ Legal/compliance approval not obtained
- ❌ Operator training incomplete
- ❌ Safety boundary bypass discovered

**Decision Authority:**
- Product Lead + Engineering Lead + Compliance Lead (consensus required)

**Timeline:**
- Pre-launch checklist completion: T-3 days
- Go/no-go decision: T-1 day
- Pilot launch: T-0 (if all GO)

---

## Appendix: References and Quick Links

**Locked Technical Checkpoints:**
- Phase 7 controlled delivery: commit 7f230d1, tag button2-phase7-controlled-delivery-release-signoff-bundle-v1
- Phase 5 PDF generation: commit 2f8fcee, tag button2-customer-pdf-phase5-customer-ready-status-final-handoff-v1
- Commercial readiness: commit b5b9abe, tag commercial-release-readiness-index-v1

**Documentation Files:**
- docs/button2_phase7_controlled_delivery_release_governance_package_v1.md (governance)
- docs/button2_phase7_controlled_delivery_final_handoff_v1.md (handoff)
- docs/commercial-release-readiness-index-v1.md (readiness)

**Smoke Evidence:**
- ops/release_checks/button2_phase7_controlled_delivery_live_smoke_evidence_checkpoint_v1/smoke_summary.json

**Support Contacts (Placeholders):**
- pilot-support@ai-risa.internal
- pilot-escalation@ai-risa.internal
- pilot-emergency@ai-risa.internal

**Legal/Compliance Templates (Placeholders):**
- legal/templates/pilot-nda-standard-v1.docx
- legal/templates/pilot-liability-waiver-v1.docx
- legal/templates/dpa-gdpr-v1.docx

---

**Pack Completed:** 2026-05-18  
**Pack Status:** Operator Readiness Documentation (Docs/Ops Only, No Code)  
**Implementation Status:** FROZEN — No product code changes  
**Next Step:** Management approval for paid-pilot launch (T-3 days before launch)
