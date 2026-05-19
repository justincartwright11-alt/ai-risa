# AI-RISA Paid-Pilot Phase 1 — Management Decision Record v1

**Decision Status: PENDING MANAGEMENT DECISION**

---

## 1. Decision Summary

**Decision:** PENDING MANAGEMENT DECISION  
**Decision Date:** May 19, 2026  
**Product Ready Status:** TECHNICALLY READY FOR PILOT LAUNCH  
**Next Approval Step:** Management/business sign-off required before launch

### Critical Note
This record confirms that AI-RISA Premium Report Factory has completed all required technical validation for paid-pilot entry. **Decision is contingent on final business/management approval.** Without sign-off, the product remains in locked-ready state but does not launch.

---

## 2. Readiness Evidence

### Button 1: READY
- **Status:** Functional baseline established
- **Scope:** Discovery, queue management, operator approval gate enforced
- **Notes:** Foundation in place; integration testing in progress

### Button 2: READY
- **Status:** LOCKED and VALIDATED
- **Latest Baseline:** button2-jbalia-hard-bind-four-matchup-live-smoke-v1 @ ef1c76c
- **Test Evidence:** 24/24 validation suite passed; live smoke 4-matchup pass
- **Deliverable:** Selected-matchup PDF generation with hard-bind Jbalia template
- **Route Status:** `/api/button2/selected-matchup/generate-guarded-v1` locked
- **Open Route Status:** `/api/button2/generated-report/open` locked (HTTP 200)
- **Library Route Status:** `/api/button2/generated-report/library` locked (HTTP 200)
- **Proof:** ops/release_checks/button2_jbalia_hard_bind_four_matchup_live_smoke_v1/live_smoke_summary.json

### Button 3: GOVERNED PREVIEW READY
- **Status:** Auto-discovery + comparison engine functional
- **Governance:** Full operator approval gate enforced; no learning/calibration write-through
- **Scope:** Result search, accuracy comparison, preview-only (no mutations)
- **Notes:** Ready for bounded preview engagement; escalation workflow confirmed

### Runtime Launcher/Preflight
- **Status:** LOCKED
- **Script:** scripts/start_ai_risa_dashboard_windows.ps1
- **Port:** http://127.0.0.1:5050
- **Environment:** Python 3.14.3 + Flask + PDFKit stack validated

### PDF Library/Open Routes
- **Status:** LOCKED
- **Library Route:** `/api/button2/generated-report/library` — HTTP 200, exact filename listing
- **Open Route:** `/api/button2/generated-report/open` — HTTP 200, fresh file delivery
- **Stale Reuse Protection:** Disabled; fresh generation enforced
- **Proof:** All 4 live smoke matchups verified open route 200 + library listing exact filename

---

## 3. Locked Technical Baseline

### Button 2 Non-Regression Anchors

| Slice | Commit | Tag | Purpose |
|-------|--------|-----|---------|
| button2-disable-section-card-engine-and-force-jbalia-premium-renderer-v1 | 9adc303 | button2-disable-section-card-engine-and-force-jbalia-premium-renderer-v1 | Disable legacy card engine; force template pack render |
| button2-selected-matchup-live-route-output-path-repair-v1 | e0a2fd0 | button2-selected-matchup-live-route-output-path-repair-v1 | Fix output path routing; enable exact filename tracking |
| button2-jbalia-template-sample-renderer-hard-bind-v1 | caba638 | button2-jbalia-template-sample-renderer-hard-bind-v1 | Hard-bind selected-matchup to Jbalia template renderer |
| button2-jbalia-hard-bind-four-matchup-live-smoke-v1 | ef1c76c | button2-jbalia-hard-bind-four-matchup-live-smoke-v1 | Four-matchup live runtime smoke proof |

### Validation Summary
- **Unit Test Bundle:** 24/24 passed
- **Live Smoke Gates:** 13/13 passed (24 pages, Jbalia profile, no stale reuse, cover/dashboard markers, forbidden scan clean, open route 200, library route 200, exact filename listed, governance false)
- **Release Checks:** All evidence artifacts committed and tagged

---

## 4. Pilot Scope

### What is Allowed in Phase 1

#### Button 1: Discovery & Queue
- Auto-web search for upcoming event cards (manual paste allowed)
- Fighter A vs Fighter B extraction and analysis
- Queue save with operator approval gate
- Report readiness ranking
- Global database write (after operator approval)

#### Button 2: PDF Generation
- Selected-matchup selection from discovered/saved fights
- Premium PDF report generation (Button 2 v29 composition, 24 pages)
- Customer-ready PDF export with Jbalia template hierarchy
- File delivery via open route and library listing

#### Button 3: Result Search & Comparison
- Auto-web search for real-life fight results (manual paste allowed)
- Result matching to saved fights/reports
- Accuracy comparison display (single fighter, matchup, event-card, segment, total)
- Preview-only comparison (no learning/calibration write-through)

#### Supporting Infrastructure
- Operator dashboard access (limited to approved staff)
- Report PDF library and download
- Governance audit trails (all decisions logged)
- Preflight/launcher status checks

### What is NOT Allowed in Phase 1

- Customer direct access to dashboard (operator-only interface)
- Learning/calibration database mutations or auto-updates
- Delivery expansion to external APIs or third-party services
- Queue purge or bulk deletion without operator approval
- Report modifications post-generation (PDFs are immutable after creation)
- Button 3 learning write-through (comparison display only)

---

## 5. Out-of-Scope Items

- Button 3 full learning/calibration loop (Phase 2+)
- Commercial multi-tenant dashboard (Phase 2+)
- Batch processing or scheduled automation (Phase 2+)
- Advanced filtering/search UI (Phase 2+)
- Customer self-service portal (Phase 3+)

---

## 6. Launch Conditions

**All conditions below must be confirmed before Phase 1 launch:**

- [ ] Customer identified and approved
- [ ] Pilot pricing and contract signed
- [ ] Support channel (email/Slack/ticket system) ready
- [ ] Operator assigned and trained
- [ ] Report delivery workflow confirmed (PDF export path, scheduling, SLA)
- [ ] Legal/commercial disclaimers reviewed and accepted
- [ ] Baseline PDF template approved (Jbalia style, 24 pages, footer branding)
- [ ] Pilot success metrics defined (accuracy, time-to-report, operator satisfaction)

---

## 7. Required Sign-Offs

**Note:** The following sign-offs are required before moving from PENDING to GO decision:

| Role | Required | Approval Status |
|------|----------|-----------------|
| Product Lead | YES | **PENDING** |
| Engineering Lead | YES | **PENDING** |
| Operations Lead | YES | **PENDING** |
| Compliance/Legal | YES | **PENDING** |
| Business Owner | YES | **PENDING** |

**Signature Block (to be completed):**

```
Product Lead:  _____________________  Date: _________
Engineering Lead:  _____________________  Date: _________
Operations Lead:  _____________________  Date: _________
Compliance/Legal:  _____________________  Date: _________
Business Owner:  _____________________  Date: _________
```

---

## 8. Blockers / Conditions

### Before Launch (Hard Requirements)
1. **All sign-offs collected and recorded** (see Section 7)
2. **Customer contract executed** with specific SLA, pricing, term
3. **Operator training completed** and documented
4. **PDF delivery endpoint validated** in production environment
5. **Backup/disaster recovery plan** for operator dashboard
6. **Incident response playbook** for PDF delivery failures

### During Pilot (Rolling Requirements)
1. **Weekly operator satisfaction check-in**
2. **Accuracy metrics tracked** (real result vs AI-RISA prediction)
3. **PDF generation latency monitored** (target: <60s per report)
4. **No unscheduled downtime** exceeding 2 hours
5. **Operator issue tickets resolved** within 24 hours

### Before Scaling (Gate for Phase 2)
1. **Pilot completion checklist signed off**
2. **Accuracy improvement opportunity identified** from Phase 1 data
3. **Button 3 learning approach designed** (design-first, before Phase 2 implementation)
4. **Multi-tenant architecture spec** reviewed for Phase 2 readiness

---

## 9. Final Approved Next Action

**Current State:** TECHNICALLY READY, AWAITING MANAGEMENT DECISION

**If GO is approved:**
1. Collect and record all sign-offs (Section 7)
2. Execute customer contract
3. Conduct operator training
4. Deploy to pilot production environment
5. Generate first customer report
6. Begin weekly check-in cadence

**If CONDITIONAL GO:**
1. Document specific conditions blocking full GO
2. Assign owner to each condition
3. Schedule re-review date
4. Record in decision record update

**If NO-GO:**
1. Document blocking reason(s)
2. Identify mitigation steps
3. Schedule re-assessment date
4. Record in decision record update

---

## Decision Record Metadata

| Field | Value |
|-------|-------|
| Record Version | v1 |
| Created | May 19, 2026 |
| Last Updated | May 19, 2026 |
| Product | AI-RISA Premium Report Factory |
| Phase | Paid-Pilot Phase 1 |
| Status | PENDING MANAGEMENT DECISION |
| Technical Validation | COMPLETE |
| Business Approval | AWAITING SIGN-OFF |

---

## Evidence Artifacts

- Live smoke summary: ops/release_checks/button2_jbalia_hard_bind_four_matchup_live_smoke_v1/live_smoke_summary.json
- Validation bundle results: operator_dashboard/test_button2_*.py (24 passed)
- Button 2 technical baseline: commits 9adc303, e0a2fd0, caba638, ef1c76c
- Runtime launcher: scripts/start_ai_risa_dashboard_windows.ps1
