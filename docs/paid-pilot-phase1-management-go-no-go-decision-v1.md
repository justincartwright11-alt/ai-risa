# Paid-Pilot Phase 1 Management Go/No-Go Decision v1

**Document Type:** Management Decision Gate (Docs/Business Only)  
**Date:** 2026-05-18  
**Status:** Decision Framework and Criteria (No Implementation)  
**Locked Checkpoint:** paid-pilot-phase1-operator-readiness-pack-v1 (commit dfbbe3c)  
**Decision Authority:** Product Lead + Engineering Lead + Compliance Lead  
**Target Decision Date:** T-3 days before pilot launch

---

## Executive Summary

This document locks the management go/no-go decision criteria for AI-RISA paid-pilot Phase 1 launch. The pilot targets 3–5 initial paying customers over a 2–4 week window with Button 2 premium PDF generation and Phase 7 controlled delivery governance.

**Current Status:** All locked checkpoints in place. Ready for management review and go/no-go decision.

---

## Decision Framework

### 1. Go Decision Requirements (ALL Must Pass)

**1.1 Technical Readiness (Engineering)**

- ✅ Phase 7 regression tests: 99/99 passing
- ✅ Phase 7 smoke tests: 10/10 passing
- ✅ Button 2 Phase 5 tests: 221+ passing
- ✅ No known critical bugs in Button 2 PDF generation
- ✅ No known critical bugs in Phase 7 controlled delivery
- ✅ Preflight check (preview endpoint) verified for all scenarios
- ✅ Delivery action (action endpoint) verified for all scenarios
- ✅ Evidence records (audit, proof, receipt) generate correctly
- ✅ Dashboard evidence display verified and visible
- ✅ Backup and disaster recovery tested
- ✅ Deployment checklist completed

**Technical Sign-Off Required:** Engineering Lead

**Evidence:**
- docs/button2_phase7_controlled_delivery_release_signoff_bundle_v1.md
- docs/button2_phase7_controlled_delivery_live_smoke_evidence_checkpoint_v1.md
- ops/release_checks/.../smoke_summary.json

---

**1.2 Safety/Governance Readiness (Engineering + Compliance)**

- ✅ Operator approval gates are mandatory (cannot be bypassed)
- ✅ Draft/internal blocking is enforced (hard stop, no override)
- ✅ Denial paths are explicit and non-executing
- ✅ manual_export channel is only active channel (no email sends, no API calls)
- ✅ Evidence retention is immutable and auditable
- ✅ No uncontrolled delivery paths exist
- ✅ No Button 1 mutation side effects from delivery actions
- ✅ No Button 3 mutation side effects from delivery actions
- ✅ No learning/calibration write expansion in Phase 1

**Safety Sign-Off Required:** Engineering Lead + Compliance Lead

**Evidence:**
- docs/button2_phase7_controlled_delivery_release_governance_package_v1.md
- docs/paid-pilot-phase1-operator-readiness-pack-v1.md (section 4: Delivery Rules)

---

**1.3 Operational Readiness (Operations)**

- ✅ Pilot database provisioned and backed up
- ✅ Customer accounts created and tested
- ✅ API keys generated (if required)
- ✅ Secure download links configured (7-day expiry)
- ✅ Audit logging enabled and verified
- ✅ Operator training completed
- ✅ Operator runbook tested with sample workflow
- ✅ Support infrastructure in place (channels, escalation)
- ✅ On-call rotation defined for pilot period

**Ops Sign-Off Required:** Operations Lead

**Evidence:**
- docs/paid-pilot-phase1-operator-readiness-pack-v1.md (section 1: Operator Runbook)

---

**1.4 Compliance/Legal Readiness (Legal + Compliance)**

- ✅ Customer NDA signed by all pilot customers (≥3 customers)
- ✅ Liability waiver in customer agreements
- ✅ Confidentiality clauses reviewed and approved
- ✅ Support SLA formally documented
- ✅ Data retention policy defined (2-year audit minimum)
- ✅ Data deletion process defined (90-day retention for PDFs)
- ✅ Security review completed (download links, file access)
- ✅ Privacy review completed (no training data leakage)
- ✅ GDPR/CCPA review completed (if customer in EU/CA)
- ✅ Audit trail immutability verified for compliance

**Compliance Sign-Off Required:** Legal Lead + Compliance Lead

**Evidence:**
- docs/paid-pilot-phase1-operator-readiness-pack-v1.md (section 6: Legal/Compliance Checklist)

---

**1.5 Customer/Business Readiness (Commercial)**

- ✅ Pilot customer 1 contract signed, account created, onboarding scheduled
- ✅ Pilot customer 2 contract signed, account created, onboarding scheduled
- ✅ Pilot customer 3 contract signed, account created, onboarding scheduled
- ✅ (Optional) Pilot customers 4–5: contracts signed (if resource allows)
- ✅ Pilot pricing confirmed (recommend 50% discount for feedback value)
- ✅ Invoicing configured and payment terms agreed
- ✅ Customer success team assigned (1–2 dedicated staff)
- ✅ Weekly customer feedback process scheduled
- ✅ Pilot success KPIs defined (NPS ≥7/10, efficiency ≥5 deliveries/hour, zero critical bugs)

**Business Sign-Off Required:** Product Lead + Commercial Lead

**Evidence:**
- Signed customer SOWs (contracts)
- Customer account setup confirmation
- docs/paid-pilot-phase1-operator-readiness-pack-v1.md (section 2: Customer Onboarding, section 8: Go/No-Go Checklist)

---

### 2. No-Go Decision Criteria (ANY May Block)

**2.1 Technical Blockers (Block Launch)**

- ❌ Any regression test fails (should be 99/99)
- ❌ Any smoke test fails (should be 10/10)
- ❌ Critical bug discovered in Phase 7 delivery
- ❌ Preflight check produces false positives or false negatives
- ❌ Evidence records do not generate correctly
- ❌ Dashboard evidence display not visible or incorrect
- ❌ Uncontrolled delivery path discovered
- ❌ Backup/disaster recovery test fails

**Resolution:** Fix critical bug, re-run tests, re-validate, reschedule launch

---

**2.2 Safety/Governance Blockers (Block Launch)**

- ❌ Operator approval can be bypassed
- ❌ Draft/internal blocking can be overridden
- ❌ Denial paths are not enforced
- ❌ email_scaffold or api_scaffold accidentally activated (real sends/calls)
- ❌ Evidence retention is mutable or incomplete
- ❌ Button 1 or Button 3 mutation observed from delivery actions
- ❌ Learning/calibration writes observed in Phase 1

**Resolution:** Investigate root cause, apply fix, re-verify safety gates, reschedule launch

---

**2.3 Operational Blockers (Block Launch)**

- ❌ Operator training incomplete or unsuccessful
- ❌ Operator runbook not tested with sample workflow
- ❌ Support channels not operational
- ❌ Customer account provisioning failed or incomplete
- ❌ Database backup failed or untested
- ❌ On-call rotation not defined

**Resolution:** Complete training, test procedures, verify infrastructure, reschedule launch

---

**2.4 Compliance/Legal Blockers (Block Launch)**

- ❌ Any customer NDA not signed (minimum 3 customers required)
- ❌ Legal review of agreements not completed
- ❌ GDPR/CCPA compliance review not completed (if applicable)
- ❌ Data retention policy not approved by Compliance
- ❌ Audit trail immutability not verified

**Resolution:** Complete legal review, obtain signatures, reschedule launch

---

**2.5 Customer/Business Blockers (Block Launch)**

- ❌ Fewer than 3 pilot customer contracts signed
- ❌ Pilot pricing not confirmed
- ❌ Customer success team not assigned
- ❌ Pilot KPIs not defined
- ❌ Invoicing not configured

**Resolution:** Finalize customer contracts, confirm pricing, assign team, reschedule launch

---

## Decision Template

### Go/No-Go Checklist (T-1 day before launch)

**Technical Readiness:**
- [ ] Engineering Lead: SIGN-OFF ☐ or BLOCK ☐
  - If BLOCK: Reason: ___________
  - Resolution required by: ___________

**Safety/Governance Readiness:**
- [ ] Compliance Lead: SIGN-OFF ☐ or BLOCK ☐
  - If BLOCK: Reason: ___________
  - Resolution required by: ___________

**Operational Readiness:**
- [ ] Operations Lead: SIGN-OFF ☐ or BLOCK ☐
  - If BLOCK: Reason: ___________
  - Resolution required by: ___________

**Legal/Compliance Readiness:**
- [ ] Legal Lead: SIGN-OFF ☐ or BLOCK ☐
  - If BLOCK: Reason: ___________
  - Resolution required by: ___________

**Business/Customer Readiness:**
- [ ] Product Lead: SIGN-OFF ☐ or BLOCK ☐
  - If BLOCK: Reason: ___________
  - Resolution required by: ___________

**Final Decision Authority:**
- [ ] Product Lead + Engineering Lead + Compliance Lead: **GO** ☐ or **NO-GO** ☐
  - GO: Proceed with pilot launch on [DATE]
  - NO-GO: Reason: ___________; Reschedule for [DATE]

---

## Timeline

### T-7 days (1 week before launch)
- Final operator training completed
- All customer contracts signed and accounts created
- Database and infrastructure fully provisioned
- Go/no-go checklist template distributed to decision authority

### T-5 days (Friday)
- Technical validation completed and signed off
- Safety/governance validation completed and signed off
- Ops readiness review completed
- Legal/compliance final review completed
- Customer onboarding materials finalized

### T-3 days (Sunday evening / Monday morning)
- **Management Go/No-Go Review Meeting**
- All stakeholders present (Product, Engineering, Ops, Legal, Compliance, Commercial)
- Review all sign-offs and blockers (if any)
- **Consensus decision: GO or NO-GO**
- If GO: Approve for launch at T-0
- If NO-GO: Identify blockers, reschedule, assign owners for fixes

### T-1 day (Day before launch)
- If GO decision made: Final checklist verification
- Customer notification: "Pilot launches tomorrow"
- Operator final walkthrough
- Support team standby

### T-0 (Launch day)
- Pilot customers have access to AI-RISA dashboard
- First fight queues entered
- First PDFs generated and delivered
- Evidence audit trail begins

---

## Success Metrics (Week 1–4 Pilot)

**Primary Metrics:**
- Customer NPS: Target ≥7/10 (9–10 = promoter, 7–8 = passive, 0–6 = detractor)
- Operator efficiency: Target ≥5 delivered reports per hour
- Critical bugs: Target 0 (zero critical production issues)
- Preflight accuracy: 100% (zero false positives, zero false negatives)
- Evidence completeness: 100% (all deliveries have audit trail)

**Secondary Metrics:**
- Time-to-PDF: Average <60 seconds
- Time-to-delivery-approval: Average <5 minutes
- Customer support tickets: <2 per week
- Operator satisfaction: Runbook clarity feedback, recommended changes

**Pilot Success Criteria (At End of Week 4):**
- NPS ≥7/10 from all 3 pilot customers
- Zero critical bugs
- Operator efficiency confirmed ≥5/hour
- No uncontrolled delivery incidents
- Customer feedback informs Phase 2 scope (Button 1 auto-discovery vs. other features)

---

## Phase 2 Decision (After Pilot Completes)

**Phase 2 Scope Depends On Pilot Feedback:**

**If Customer Feedback Requests Button 1 Auto-Discovery:**
- Design auto-discovery ranking + review UX
- Implement discovery + ranking logic
- Regression + smoke testing
- Deploy to pilot customers in Phase 2 (Week 5–6)

**If Customer Feedback Requests Button 3 Learning:**
- Design result matching + comparison logic
- Implement learning/calibration gates
- Regression + smoke testing
- Deploy to pilot customers in Phase 3+ (not Phase 2)

**If Customer Feedback is Positive / No New Requests:**
- Prepare for commercial launch with current Button 2 scope
- Scale from 3–5 pilot customers to 20–50 paying customers
- Launch commercial product with same Phase 7 governance

**Hard Rule (Maintained):**
No product code changes until paid-pilot Phase 1 completes and real customer feedback defines Phase 2 scope.

---

## Risk Mitigation

### Technical Risk: Critical Bug in Delivery
**Likelihood:** Low (99/99 tests passing, 10/10 smoke passing)  
**Impact:** High (customers cannot deliver reports)  
**Mitigation:**
- Extensive test coverage (99 regression tests)
- Smoke testing before launch (10 checks)
- On-call engineering team during pilot
- Rollback plan if critical bug discovered (revert to previous locked commit)

### Operational Risk: Operator Error
**Likelihood:** Medium (new workflow for operators)  
**Impact:** Medium (delivery delayed or denied incorrectly)  
**Mitigation:**
- Comprehensive operator runbook
- Operator training and certification before launch
- Clear denial messages in dashboard
- Support escalation path for operator questions

### Compliance Risk: Audit Trail Incomplete
**Likelihood:** Low (audit logging verified)  
**Impact:** High (compliance failure, regulatory issue)  
**Mitigation:**
- Audit logging enabled and tested
- Evidence records retained for 2 years
- Monthly audit log review during pilot
- Compliance team monitoring during pilot

### Customer Risk: Unmet Expectations
**Likelihood:** Medium (PDF depth/quality variable by fight)  
**Impact:** Medium (pilot customer churn)  
**Mitigation:**
- Set expectations in onboarding (26 pages, probabilistic predictions)
- Weekly customer feedback collection
- Quick response to quality issues
- Customer success team assigned 1:1

### Business Risk: Pricing Too Low / Too High
**Likelihood:** Low (50% discount tested with advisory customers)  
**Impact:** Medium (revenue loss or customer rejection)  
**Mitigation:**
- 50% discount recommended for Phase 1 (get feedback value)
- Collect pricing feedback from pilot customers
- Adjust pricing for Phase 2 based on pilot results

---

## Escalation Path

**If Blocker Discovered During Pilot (Week 1–4):**

1. **Severity: Critical** (prevents all deliveries)
   - Escalate to Engineering + Product Lead immediately
   - Halt pilot for affected customer if needed
   - Target resolution: <2 hours

2. **Severity: High** (prevents some deliveries, safety concern)
   - Escalate to Engineering + Compliance within 30 minutes
   - Continue pilot with workaround if possible
   - Target resolution: <24 hours

3. **Severity: Medium** (operational issue, no safety concern)
   - Log in support system
   - Address by end of business day
   - Collect for Phase 2 improvements

4. **Severity: Low** (cosmetic, polish)
   - Log for Phase 2 improvements
   - Address after pilot if time permits

---

## Locked Sequence (Ready for Decision)

| Checkpoint | Commit | Tag | Status |
|-----------|--------|-----|--------|
| Phase 7 Release Signoff | 7f230d1 | button2-phase7-controlled-delivery-release-signoff-bundle-v1 | ✅ Locked |
| Commercial Readiness | b5b9abe | commercial-release-readiness-index-v1 | ✅ Locked |
| Operator Readiness Pack | dfbbe3c | paid-pilot-phase1-operator-readiness-pack-v1 | ✅ Locked |
| **Management Decision Gate** | **PENDING** | **paid-pilot-phase1-management-go-no-go-decision-v1** | **← AWAITING** |

---

## Hard Rules (Maintained)

1. **No product code changes until Paid-Pilot Phase 1 completes** and real customer feedback defines Phase 2 scope.
2. **All test suites must pass** (99/99 regression, 10/10 smoke) before launch and during pilot.
3. **Operator approval is mandatory** before every customer delivery (cannot be bypassed).
4. **Draft/internal blocking is enforced** (hard stop, no override).
5. **Evidence retention is immutable** (audit trail retained for 2+ years for compliance).
6. **Phase 7 governance is frozen** (no delivery expansion without new slice authorization).

---

## Decision Record Template

**For Management Decision Authority to Complete on Decision Date:**

```
PAID-PILOT PHASE 1 GO/NO-GO DECISION
Date: [DATE]
Decision Authority: [Product Lead], [Engineering Lead], [Compliance Lead]

SIGN-OFFS:
☐ Engineering Lead: GO / NO-GO
☐ Compliance Lead: GO / NO-GO
☐ Operations Lead: GO / NO-GO
☐ Legal Lead: GO / NO-GO
☐ Product Lead: GO / NO-GO

CONSENSUS DECISION: **GO** / **NO-GO**

If GO:
- Pilot launch approved for [DATE]
- Pilot duration: 2–4 weeks
- Target customers: 3–5 (names: ____________)
- Success criteria: NPS ≥7/10, zero critical bugs, operator efficiency ≥5/hour

If NO-GO:
- Blocker: ___________________
- Owner for resolution: ___________________
- Target resolution date: ___________________
- Rescheduled launch date: ___________________

Signed:
___________________________ (Product Lead)
___________________________ (Engineering Lead)
___________________________ (Compliance Lead)
```

---

## Next Steps After GO Decision

**If Management Decision is GO:**

1. **T-1 day:** Final all-hands pilot kickoff meeting
2. **T-0:** Pilot launch; customer access enabled
3. **Week 1:** Daily standup with customer + operator + engineering
4. **Week 2:** Mid-pilot check-in; customer feedback collection
5. **Week 4:** End-of-pilot review; Phase 2 scope definition
6. **Week 5:** Phase 2 decision: Continue, escalate, or adjust

**If Management Decision is NO-GO:**

1. Identify and fix blocker
2. Reschedule decision meeting for [SPECIFIC DATE]
3. No code changes permitted until blocker resolved
4. Implementation remains frozen

---

**Decision Gate Opened:** 2026-05-18  
**Decision Gate Status:** Ready for Management Review (All Checkpoints Locked)  
**Target Decision Date:** T-3 days before pilot launch (specific date TBD by management)  
**Decision Authority Required:** Product Lead, Engineering Lead, Compliance Lead (consensus)

---

## Appendix: Reference Documents

**Locked Technical Checkpoints:**
- Phase 7: commit 7f230d1, tag button2-phase7-controlled-delivery-release-signoff-bundle-v1
- Commercial Readiness: commit b5b9abe, tag commercial-release-readiness-index-v1
- Operator Pack: commit dfbbe3c, tag paid-pilot-phase1-operator-readiness-pack-v1

**Key Documentation:**
- docs/button2_phase7_controlled_delivery_release_governance_package_v1.md
- docs/paid-pilot-phase1-operator-readiness-pack-v1.md
- ops/release_checks/.../smoke_summary.json

**Support Contacts:**
- Product Lead: [NAME/EMAIL]
- Engineering Lead: [NAME/EMAIL]
- Compliance Lead: [NAME/EMAIL]
- Operations Lead: [NAME/EMAIL]
- Legal Lead: [NAME/EMAIL]
