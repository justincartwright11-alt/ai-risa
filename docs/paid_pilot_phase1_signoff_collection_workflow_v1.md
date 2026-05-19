# AI-RISA Paid-Pilot Phase 1 — Sign-Off Collection Workflow v1

## Purpose

This workflow defines the process for collecting the five required management approvals needed to move the paid-pilot phase 1 decision from **PENDING MANAGEMENT DECISION** to **GO**, **CONDITIONAL GO**, or **NO-GO**.

---

## 1. Required Sign-Off Roles

| # | Role | Department | Key Responsibility |
|---|------|------------|-------------------|
| 1 | Product Lead | Product/Strategy | Feature completeness, customer value, roadmap alignment |
| 2 | Engineering Lead | Engineering | Technical readiness, code quality, maintainability |
| 3 | Operations Lead | Operations | Deployment readiness, support capability, SLA feasibility |
| 4 | Compliance/Legal | Legal/Compliance | Data privacy, liability, contract terms, regulatory requirements |
| 5 | Business Owner | Executive/Finance | Business case viability, pilot ROI, customer fit |

---

## 2. Approval Questions for Each Role

### Product Lead

**Must Review:**
- [x] Button 2 PDF generation quality meets customer expectations (24 pages, Jbalia template hierarchy, cover markers present)
- [x] Button 1 discovery + queue workflow supports operator experience
- [x] Button 3 comparison preview provides actionable accuracy feedback
- [x] Operator dashboard is intuitive and requires minimal training

**Approval Question:**
> *Do you confirm that AI-RISA Premium Report Factory is feature-complete and ready for paid-pilot engagement with the customer?*

**Acceptable Responses:**
- **GO:** All features validated; customer expectations met; ready to launch
- **CONDITIONAL GO:** Features acceptable with documented limitations; customer aware of constraints
- **NO-GO:** Features do not meet minimum requirements; recommend further development before pilot

### Engineering Lead

**Must Review:**
- [x] Button 2 technical baseline locked (commits 9adc303, e0a2fd0, caba638, ef1c76c)
- [x] Live smoke validation passed (13/13 gates, 24 pages, Jbalia profile, no stale reuse, governance false)
- [x] Unit test bundle passed (24/24 tests)
- [x] Runtime launcher and PDF routes operational and tested

**Approval Question:**
> *Do you confirm that the technical baseline is stable, tested, and production-ready for pilot deployment?*

**Acceptable Responses:**
- **GO:** All systems validated and locked; ready for production deployment
- **CONDITIONAL GO:** Systems functional with known edge cases documented; monitoring required
- **NO-GO:** Technical issues require resolution before pilot deployment

### Operations Lead

**Must Review:**
- [x] Operator dashboard training requirements and time-to-proficiency
- [x] PDF delivery workflow (export path, scheduling, SLA: <60s per report)
- [x] Backup/disaster recovery plan for operator dashboard
- [x] Incident response playbook for PDF delivery failures
- [x] Support ticket resolution workflow and SLA (24 hours)
- [x] Weekly check-in cadence and metrics tracking (accuracy, latency, uptime)

**Approval Question:**
> *Do you confirm that operations infrastructure, staffing, and support processes are ready to support the pilot customer?*

**Acceptable Responses:**
- **GO:** Operations fully prepared; staffing confirmed; support workflows locked
- **CONDITIONAL GO:** Operations prepared with noted gaps; mitigation plan documented; requires weekly check-ins
- **NO-GO:** Operations not ready; recommend timeline extension before pilot launch

### Compliance/Legal

**Must Review:**
- [x] Data privacy assessment (operator-only access, governance audit trails, no customer PII in PDFs)
- [x] Liability review (PDF disclaimers, accuracy caveats, "not a guarantee" language present)
- [x] Contract terms with customer (SLA, pilot duration, IP ownership, termination clauses)
- [x] Regulatory requirements (if applicable by jurisdiction)
- [x] Insurance coverage for pilot engagement

**Approval Question:**
> *Do you confirm that legal and compliance requirements are met and documentation is acceptable for pilot engagement?*

**Acceptable Responses:**
- **GO:** All compliance and legal requirements satisfied; ready for customer engagement
- **CONDITIONAL GO:** Requirements mostly met with documented exceptions; legal review scheduled post-pilot
- **NO-GO:** Compliance or legal issues must be resolved before pilot launch

### Business Owner

**Must Review:**
- [x] Pilot customer identified and qualified
- [x] Pricing and contract economics viable
- [x] Pilot ROI projection and success metrics
- [x] Market opportunity validation (post-pilot scaling potential)
- [x] Budget approved for pilot support costs
- [x] Executive sponsor assigned

**Approval Question:**
> *Do you confirm that the business case is sound, customer is qualified, and budget is authorized for the pilot engagement?*

**Acceptable Responses:**
- **GO:** Business case validated; customer qualified; budget approved; ready to execute
- **CONDITIONAL GO:** Business case acceptable with conditions; customer TBD; requires approval before first report generation
- **NO-GO:** Business case not viable; recommend pilot postponement or redesign

---

## 3. Evidence Each Role Must Review

### All Roles (Common Evidence)
- docs/paid_pilot_phase1_management_decision_record_v1.md
- ops/release_checks/button2_jbalia_hard_bind_four_matchup_live_smoke_v1/live_smoke_summary.json

### Product Lead
- ops/release_checks/button2_jbalia_template_sample_renderer_hard_bind_v1/visual_proof/ (cover/dashboard screenshots)
- Customer feedback (if pilot customer already identified)
- Button 1 queue UI/UX documentation
- Button 3 comparison preview mockup

### Engineering Lead
- operator_dashboard/test_button2_jbalia_template_sample_renderer_hard_bind_v1.py (24/24 passed)
- Full validation test suite results
- Git commit history: 9adc303, e0a2fd0, caba638, ef1c76c
- Runtime launcher script: scripts/start_ai_risa_dashboard_windows.ps1
- Technical baseline documentation

### Operations Lead
- Operator training curriculum
- PDF delivery workflow diagram
- Backup/disaster recovery plan
- Incident response playbook
- Support ticket SLA documentation
- Weekly metrics tracking template

### Compliance/Legal
- Data privacy impact assessment
- PDF disclaimer language review
- Customer contract draft (SLA, pricing, term, IP, termination)
- Regulatory checklist (jurisdiction-specific)
- Insurance coverage confirmation

### Business Owner
- Customer qualification checklist
- Pricing/contract economics model
- Pilot ROI projection
- Market opportunity analysis
- Budget approval documentation
- Executive sponsor assignment

---

## 4. GO / CONDITIONAL GO / NO-GO Criteria

### GO Criteria (All Required)
- [x] Product Lead: GO
- [x] Engineering Lead: GO
- [x] Operations Lead: GO
- [x] Compliance/Legal: GO
- [x] Business Owner: GO
- [x] All launch condition checklist items: CONFIRMED
- [x] Customer identified and contract signed
- [x] Operator trained and assigned

**Outcome:** Immediate pilot launch authorization

### CONDITIONAL GO Criteria (At Least 4 Required, with Documented Exceptions)
- 4 or 5 roles approve with conditions
- Conditions are documented and owned
- Mitigation plan for each condition is approved
- Re-review date scheduled

**Outcome:** Pilot launch authorized with conditions; weekly check-ins required; escalation path defined

### NO-GO Criteria (Any Role Blocks)
- Any role votes NO-GO
- Blocking issue(s) identified
- Mitigation path unclear or infeasible
- Re-review date scheduled after mitigation

**Outcome:** Pilot launch postponed; development/resolution work defined; decision re-opened after remediation

---

## 5. Launch Condition Checklist

| # | Condition | Responsible | Status | Evidence |
|---|-----------|-------------|--------|----------|
| 1 | Customer identified and approved | Business Owner | PENDING | Customer contract |
| 2 | Pilot pricing and contract signed | Business Owner | PENDING | Signed contract |
| 3 | Support channel ready | Operations Lead | PENDING | Support ticket system setup |
| 4 | Operator assigned and trained | Operations Lead | PENDING | Training sign-off |
| 5 | Report delivery workflow confirmed | Operations Lead | PENDING | Workflow document |
| 6 | Legal/commercial disclaimers reviewed | Compliance/Legal | PENDING | Approved disclaimer text |
| 7 | Baseline PDF template approved | Product Lead | PENDING | Template review sign-off |
| 8 | Pilot success metrics defined | Business Owner + Product Lead | PENDING | Metrics document |

**All 8 items must be CONFIRMED before launch is authorized.**

---

## 6. Sign-Off Capture Template

Use this template to record each role's approval:

```markdown
### [ROLE NAME] Sign-Off

**Reviewer:** [Full Name, Title]  
**Date:** [YYYY-MM-DD]  
**Time:** [HH:MM UTC]  

**Approval Decision:**  
- [ ] GO  
- [ ] CONDITIONAL GO  
- [ ] NO-GO  

**Key Findings / Evidence Reviewed:**  
[List 3-5 key review items and outcome]

**Conditions (if CONDITIONAL GO):**  
1. [Condition 1]  
   - Mitigation: [How will this be addressed?]  
   - Owner: [Who is responsible]  
   - Timeline: [When will it be resolved?]  

2. [Condition 2]  
   - ... (repeat for each condition)

**Blocking Issues (if NO-GO):**  
1. [Issue 1]  
   - Required resolution: [What must be done]  
   - Owner: [Who is responsible]  
   - Re-review date: [When will decision be revisited?]

**Sign-Off:**  
- Signature: _____________________  
- Print Name: _____________________  
- Date: _____________________  

---
```

---

## 7. Final Update Process for paid-pilot-phase1-management-decision-record-v1

Once all five sign-offs are collected, execute this process:

### Step 1: Consolidate Sign-Offs
- Gather all five completed sign-off templates
- Verify all required fields are completed
- Calculate final decision (GO, CONDITIONAL GO, or NO-GO)

### Step 2: Update Decision Record
Edit `docs/paid_pilot_phase1_management_decision_record_v1.md`:
- Replace all "PENDING" statuses with actual outcomes (GO, CONDITIONAL GO, NO-GO)
- Add signatures and dates to sign-off block (Section 7)
- Update "Final Decision" section (Section 9) with:
  - Final status (GO / CONDITIONAL GO / NO-GO)
  - Approval date
  - Approved by (consolidating authority)
  - Next action (launch, conditions tracking, re-review, etc.)

### Step 3: Update Summary JSON
Edit `ops/release_checks/paid_pilot_phase1_management_decision_record_v1/management_decision_summary.json`:
- Update `decision_status` from "PENDING MANAGEMENT DECISION" to final status
- Update each role in `required_sign_offs` array:
  - `status`: change from "PENDING" to "GO", "CONDITIONAL GO", or "NO-GO"
  - `signature`: add approver name
  - `date`: add approval date
- Update `launch_conditions_checklist`: mark all items "CONFIRMED"
- Update `final_decision` section:
  - `status`: final decision
  - `decision_date`: approval date
  - `approved_by`: consolidating authority
  - `approval_timestamp`: ISO 8601 timestamp

### Step 4: Commit Updated Decision Record
```bash
git add docs/paid_pilot_phase1_management_decision_record_v1.md ops/release_checks/paid_pilot_phase1_management_decision_record_v1/management_decision_summary.json
git commit -m "paid-pilot-phase1-management-decision-record-v1: update with final approvals - GO / CONDITIONAL GO / NO-GO"
git tag paid-pilot-phase1-management-decision-record-signed-v1
```

### Step 5: Next Actions Based on Decision
- **If GO:** Proceed to launch preparation (deployment, customer onboarding, first report generation)
- **If CONDITIONAL GO:** Begin condition tracking; schedule weekly check-ins; escalate blockers to executive sponsor
- **If NO-GO:** Defer pilot; open Phase 2 planning or product refinement work

---

## 8. Workflow Timeline

| Day | Activity | Owner | Deliverable |
|-----|----------|-------|-------------|
| Day 1 | Distribute sign-off templates to all five roles | Workflow Coordinator | Sign-off request email |
| Day 2-3 | Roles review evidence and draft approvals | All five roles | Draft sign-off templates |
| Day 4 | Consolidate responses; identify any blockers | Workflow Coordinator | Blocker summary (if any) |
| Day 5 | Final review and consolidation | Executive Sponsor | Decision summary |
| Day 6 | Update paid-pilot-phase1-management-decision-record-v1 | Workflow Coordinator | Signed decision record |
| Day 7 | Approve and lock final decision | Executive Sponsor | Tagged decision commit |

---

## 9. Escalation Path

**If consensus cannot be reached:**
1. Document all disagreements and rationales
2. Executive sponsor reviews conflicting opinions
3. Executive sponsor makes tiebreaker decision
4. Final decision recorded with sponsor authorization

**If external factors delay approval:**
1. Notify all parties of delay reason
2. Reschedule sign-off window
3. Update timeline in decision record

---

## 10. Archive & Reference

**Approved sign-offs archived at:**
- ops/release_checks/paid_pilot_phase1_management_decision_record_v1/sign_offs/

**Sign-off templates naming convention:**
- `[ROLE_TITLE]_signoff_[DATE]_[APPROVER_INITIALS].md`
- Example: `product_lead_signoff_2026-05-22_JDoe.md`

**Final locked decision record:**
- docs/paid_pilot_phase1_management_decision_record_v1.md (updated with all approvals)
- Tag: `paid-pilot-phase1-management-decision-record-signed-v1`

---

## Workflow Execution Checklist

- [ ] All five roles receive sign-off request with evidence links
- [ ] Sign-off templates completed and returned by all roles
- [ ] No blocking issues identified (or mitigation plan approved)
- [ ] Final decision consolidated (GO / CONDITIONAL GO / NO-GO)
- [ ] Decision record updated with signatures and dates
- [ ] Summary JSON updated with final statuses
- [ ] Commit and tag created for signed decision record
- [ ] Next action authorized (launch prep, condition tracking, or re-review)

