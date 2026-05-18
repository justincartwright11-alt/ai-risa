# Button 2 Premium PDF Generation — Paid-Pilot Operator Runbook v1

**Status**: DOCS-ONLY OPERATOR GUIDE

---

## Welcome to the Button 2 Paid-Pilot

This runbook is your guide to safely and confidently evaluate Button 2 Premium PDF Generation during the paid-pilot phase.

**Duration**: 1–2 weeks  
**Test Fights**: 5–10 representative matchups  
**Operator Role**: Review, approve/reject, and report feedback  
**System Role**: Preview, proof, gate—no execution  

---

## 1. Pilot Purpose

### What We're Evaluating
Can Button 2 reliably:
- Generate comprehensive HTML report previews?
- Validate all analysis proofs and metadata?
- Help you make informed approval decisions?
- Signal when a report is ready for customer delivery?
- Keep you in control of all approval gates?

### Success Looks Like
- You understand all status signals in the preview
- You feel confident in your approval/rejection decisions
- You see the proofs and data backing each decision
- You know exactly what happens next (and what doesn't)
- No surprises, no automation bypass, no safety gaps

### Pilot Does NOT Evaluate
- ❌ Actual PDF generation (Phase 7A—next phase)
- ❌ Customer delivery (Phase 7B—after PDF works)
- ❌ Learning/calibration updates (Phase 7D—much later)
- ❌ Emergency overrides or fast-path approvals

---

## 2. What Button 2 Can Safely Do Now

### Preview & Proof Stack
✓ **Generate HTML previews** of complete fight reports (all sections)  
✓ **Display all analysis sections**: matchup analysis, fighter profiles, risk factors, method pathways, scenario trees, evidence  
✓ **Show all proof data** in the meta-footer: source traceability, header/footer/watermark validation, chart/scenario validation, page-break validation, typography validation  
✓ **Render proof payloads** so you can inspect every validation step  

### Status Signaling
✓ **Customer-ready status**: Shows "ready for customer" or "not ready" based on proof outcomes  
✓ **Controlled-export preview**: Shows "eligible for export (pending operator approval)" or "not eligible" based on customer-ready status  
✓ **Operator approval gate**: Always displays "operator approval required" (you are in control)  
✓ **Server-path policy**: Always displays "server-derived output path required" (system determines where files go, not you)  

### Decision Support
✓ **Read-only proof inspection**: You can see all data backing the status signals  
✓ **Fail-closed eligibility**: System defaults to "not ready" if any proof is missing  
✓ **Operator-driven approval**: All decisions are yours to make; no automatic actions  

---

## 3. What Button 2 Must NOT Do Yet

### Automation (Blocked Until Phase 7A+)
❌ **Do NOT generate PDF files** (preview-only HTML now)  
❌ **Do NOT download/export reports** (no export UI exposed)  
❌ **Do NOT deliver PDFs to customers** (no delivery automation)  
❌ **Do NOT auto-certify reports** (no certification automation)  

### Unsafe Operator Paths (Blocked)
❌ **Do NOT accept custom output paths** (you cannot choose where PDFs go)  
❌ **Do NOT override approval gates** (gates are non-bypassable)  
❌ **Do NOT log operator decisions to database** (nothing is recorded persistently)  
❌ **Do NOT auto-approve based on past decisions** (each fight is a fresh decision)  

### State Mutations (Blocked)
❌ **Do NOT write files during preview** (preview-only, no I/O)  
❌ **Do NOT modify database during preview** (read-only preview)  
❌ **Do NOT trigger learning updates** (Button 3 scope, not here)  
❌ **Do NOT update certification metadata** (Phase 7C scope)  

---

## 4. Operator Workflow

### Step-by-Step (Standard Flow)

**Step 1: Navigate to Button 2**
```
Main Dashboard → Button 2: Premium PDF Generation
```
You see a list of fights from Button 1 queue waiting for PDF generation.

**Step 2: Select a Test Fight**
```
Click on fight card (e.g., "Fighter A vs. Fighter B — May 18, 2026")
```
System shows basic fight info and "Generate Preview" button.

**Step 3: Request HTML Preview**
```
Click "Generate Preview"
```
System calls Button 2 engine. Takes ~2 seconds.
Returns: Full HTML preview + metadata + status rows.

**Step 4: Review Report Content**
```
Scroll through entire report in preview window:
  - Title block
  - Executive summary
  - Fighter A profile
  - Fighter B profile
  - Matchup analysis
  - Risk factors
  - Method pathways
  - Scenario tree
  - Evidence section
```
Look for any content gaps, placeholder text, or data that looks wrong.

**Step 5: Check Meta-Footer Proof Status**
```
Scroll to bottom of preview → "QA & Proof Status" section
```
Read all proof payloads. See if they're green or red.

**Step 6: Check Customer-Ready Status**
```
Find row: "Customer-ready preview: [status]"
```
- If "customer_ready_recommended" → All proofs pass, certified, ready for evaluation
- If "customer_ready_not_ready" → Missing proofs or not certified, escalate

**Step 7: Check Controlled-Export Gate**
```
Find rows:
  - "Controlled export preview: [status]"
  - "Gate: operator_approval_required"
  - "Output path policy: server_derived_output_path_required"
```
- Status should mirror customer-ready status
- Gates should always be present (they are your safety net)

**Step 8: Make Approval Decision**
```
Question: "Is this report ready for a customer to receive?"

If YES:
  1. Check all proofs are green ✓
  2. Check customer-ready says "recommended" ✓
  3. Check gates are present ✓
  4. Click "Approve for Payment System" (Phase 7+)
  → System queues for export (Phase 7A) and delivery (Phase 7B)
  
If NO (or BLOCKED):
  1. Note which proofs are red or missing
  2. Click "Escalate to Button 1" or "Mark for Review"
  3. Provide feedback to engineering (e.g., "Source citations missing")
  → Report goes back to Button 1 for remediation
```

**Step 9: Record Pilot Feedback**
```
After decision:
  1. Feedback form: "How clear was the proof status?"
  2. Feedback form: "Did you feel in control of the approval?"
  3. Feedback form: "Any questions or concerns?"
  4. Send to pilot coordinator
```

**Step 10: (Phase 1–6 End)**
```
Pilot evaluation is now complete for this fight.
Wait for next Phase 7+ iteration or test next fight.
```

---

## 5. Proof-Stack Review Steps

### What Are Proofs?

A "proof" is a system-generated validation that a specific piece of the report meets quality standards.

**6 Proof Categories**:
1. **Source Traceability** → All claims have sources; all sources are traceable
2. **Header/Footer/Watermark** → Running headers, page numbers, confidentiality labels render correctly
3. **Chart/Scenario** → Scenario trees and method pathways render without corruption
4. **Page-Break Layout** → Pages break cleanly without orphan/widow lines
5. **Typography Polish** → Fonts, sizes, spacing are consistent and readable
6. **Overlap & Off-Page** → No hidden text, no layout overflow

### How to Read Proof Status

**In Meta-Footer QA Section**:
```
Proof Category | Status | Details
──────────────────────────────────
Source Traceability | VERIFIED | 12 sources, all official tier_a
Header/Footer/Watermark | VERIFIED | Running headers present, no corruption
Chart/Scenario | VERIFIED | Scenario tree renders, 8 risk factors shown
Page-Break Layout | VERIFIED | 3 page breaks, widow/orphan rules applied
Typography Polish | VERIFIED | 11pt body, 14pt headers, consistent spacing
Overlap Proof | VERIFIED | No off-page text detected
Total Proofs | 6/6 VERIFIED | Report ready for evaluation
```

### Green vs. Red Proofs

**GREEN** (✓ VERIFIED):
- Proof passed all checks
- This part of the report is safe to share with customer

**RED** (✗ FAILED):
- Proof detected an issue
- Do NOT approve this report for customer delivery
- Escalate to engineering with proof details

### Example: Proofs Show Missing Source

**Scenario**: You click "Generate Preview" and scroll to meta-footer:
```
Proof: Source Traceability | FAILED
Issue: 2 claims in Method Pathways section have no source citation
Details: Lines 47–52 reference techniques but cite no reference
Action: ESCALATE TO BUTTON 1
```

**Your Decision**: Reject. Click "Escalate to Button 1 for Source Addition."
Reason: "Sources missing for method pathway claims."

---

## 6. Customer-Ready Status Interpretation

### What It Means

**Customer-ready status** answers one question: **"Is this report safe and complete enough to show to a paying customer?"**

### Status Values

#### customer_ready_recommended
**Meaning**: "Yes, this report is ready for customer delivery."

**When You See This**:
- ✓ All 6 proofs are green/verified
- ✓ Visual certification is complete ("certified")
- ✓ Report content is present and complete

**Your Decision Point**:
```
"Do I want to approve this for payment and delivery?"
YES → Click "Approve for Export" (Phase 7+)
NO → Click "Escalate" (explain reason in feedback)
```

**You Are In Control**: System says "ready," but you decide "approve or not."

#### customer_ready_not_ready
**Meaning**: "No, this report is not ready yet. Something is missing or failed."

**When You See This**:
- ❌ One or more proofs are red/failed
- ❌ Visual certification is missing or failed
- ❌ Report sections are incomplete

**Your Decision Point**:
```
"Should I escalate this back to Button 1?"
YES → Click "Escalate" and provide reason (e.g., "Missing sources")
NO → Can't approve. System blocks export-eligible status.
```

**No Approval Shortcut**: You cannot force a "not ready" report to "ready" status. System blocks it.

### Reading the Gate

**Always Present**:
```
Gate: operator_approval_required
```

**Meaning**: "Even if this report is customer_ready_recommended, you must approve it before we proceed. No automation. You decide."

---

## 7. Controlled-Export Preview Interpretation

### What It Means

**Controlled-export status** answers: **"If you approve this report, is it eligible for export to PDF and delivery?"**

### Status Values

#### controlled_export_eligible_pending_operator_approval
**Meaning**: "This report CAN be exported and delivered, but only if you approve it."

**When You See This**:
- ✓ Customer-ready status is "customer_ready_recommended"
- ✓ All proofs pass
- ✓ Certification is complete

**Next Action (Phase 7+)**:
```
[YOU APPROVE] → System generates PDF → System sends to customer
```

**Current Pilot** (Phase 1–6):
```
[Status shows "eligible, pending approval"]
[You see gates and policies]
[No further action until Phase 7+ is released]
```

#### controlled_export_not_eligible
**Meaning**: "This report CANNOT be exported or delivered. Something is wrong."

**When You See This**:
- ❌ Customer-ready status is "customer_ready_not_ready"
- ❌ One or more proofs failed
- ❌ Certification is missing

**Next Action**:
```
Escalate to Button 1 with reason (e.g., "Source traceability failed")
Fix → Re-generate → Re-review
```

### Reading the Policies

**Always Present**:
```
Gate: operator_approval_required
Output path policy: server_derived_output_path_required
```

**Meaning**:
- **Gate**: You must approve before export happens. System will not auto-execute.
- **Policy**: System determines the output file path. You cannot choose a custom location.

**Why This Matters**:
- You stay in control (operator approval required)
- The system stays safe (server determines paths, not operator)

---

## 8. Approval Gate Checklist

### Before You Click "Approve"

Use this checklist to confirm you're making a safe decision:

```
□ Step 1: Scrolled through entire report
   - All sections present?
   - All content looks accurate?
   - No placeholder text?
   - No corrupted data?

□ Step 2: Checked meta-footer proofs
   - All 6 proof categories present?
   - All showing VERIFIED (green)?
   - Any RED (failed) proofs? If yes, STOP. Escalate.

□ Step 3: Checked customer-ready status
   - Status shows "customer_ready_recommended"?
   - If "customer_ready_not_ready", STOP. Cannot approve.

□ Step 4: Checked export-eligible status
   - Status shows "controlled_export_eligible_pending_operator_approval"?
   - If "controlled_export_not_eligible", STOP. Cannot export.

□ Step 5: Confirmed gates are present
   - "Gate: operator_approval_required" visible?
   - "Output path policy: server_derived_output_path_required" visible?
   - If either missing, STOP. Contact engineering.

□ Step 6: Made your decision
   - Do I approve this for customer delivery? YES / NO / UNSURE
   - If YES, proceed to Step 7
   - If NO or UNSURE, escalate with reason

□ Step 7: Clicked "Approve for Payment System" (Phase 7+)
   - System queues report for export
   - (No action until Phase 7A is released)
   - Confirmation shown: "Report approved. Pending Phase 7 export."
```

### If You're Unsure

**Do NOT approve blindly.**

Ask:
1. Are all proofs green? If any red → Escalate
2. Does customer-ready say "recommended"? If not → Escalate
3. Does export-eligible say "pending approval"? If not → Escalate
4. Are gates present and visible? If not → Contact engineering

**If any question above is NO**: Escalate. Do not approve.

---

## 9. Demo Script (For New Operators)

### 5-Minute Demo Flow

**Setup**: Have a pre-generated HTML preview open in a browser window.

**1. Introduction (1 min)**
```
"This is Button 2 Premium PDF Generation. It's in paid-pilot evaluation.
Your job is to review previews and approve/reject reports.
All approval decisions are yours. The system is here to help you, not override you."
```

**2. Show Report Content (1.5 min)**
```
"Here's what you see when you request a preview:
  - The entire fight report in HTML
  - All sections: fighters, matchup analysis, scenarios, risk factors
  - Professional formatting, ready to show a customer

Let me scroll through it..."
[Scroll through all sections slowly]
"See? All content is there, nothing's missing."
```

**3. Show Meta-Footer Proof Status (1 min)**
```
"At the bottom, you see the proof status. This is where the system tells you
if the report is good to go:

[Point to each proof row]
  - Source traceability: All claims have sources ✓
  - Header/footer: Running headers and page numbers ✓
  - Charts: Scenario trees render correctly ✓
  - Page breaks: No orphan lines ✓
  - Typography: Fonts and spacing are consistent ✓
  
All green = Safe to ship"
```

**4. Show Customer-Ready Status (0.5 min)**
```
"Below that, you see:
  'Customer-ready preview: customer_ready_recommended'

This means: 'System says this is ready for customer. Your call.'"
```

**5. Show Export Gate (0.5 min)**
```
"And here's the gate that keeps you in control:
  'Gate: operator_approval_required'
  'Output path policy: server_derived_output_path_required'

Translation: 'You must approve before anything happens.
The system picks the file path, not you.'"
```

**6. Close with Decision Logic (1 min)**
```
"So here's how you decide:

Are all proofs green? YES ✓
Is it customer-ready? YES ✓
Are the gates present? YES ✓
Do I trust the content? YES ✓

Then: Click 'Approve for Payment System'
The report is queued. Phase 7+ will take it from there.

If ANY of those are NO:
Click 'Escalate' and tell us why.
Report goes back to Button 1 for fixing."
```

---

## 10. Paid-Pilot Acceptance Criteria

### Pilot Success Metrics

**Must-Have Outcomes**:
```
□ Operator understands all proof signals
  Metric: Operator can explain what each proof means without help

□ Operator feels in control of decisions
  Metric: Operator says "I made the approval decision" not "system decided"

□ No approval shortcuts or automation surprises
  Metric: Operator never sees auto-approvals or bypasses

□ Gates are always visible and non-bypassable
  Metric: Operator cannot override or ignore gates

□ Report content is accurate and complete
  Metric: No missing sections, no placeholder text, no data corruption

□ All 5–10 test fights can be evaluated without error
  Metric: 100% success rate; zero crashes or timeouts
```

### Pilot Feedback Template

**After each report evaluation**, complete this:

```
Report: [Fighter A vs. Fighter B — Date]
Approved: YES / NO / ESCALATED

Feedback:
1. Clarity of proof status (1–5 stars): ___
   Comments: [e.g., "Proof names were clear, easy to understand"]

2. Confidence in your approval decision (1–5 stars): ___
   Comments: [e.g., "All data present, felt safe approving"]

3. Gate visibility and control (1–5 stars): ___
   Comments: [e.g., "Gates were obvious; felt like I had final say"]

4. Any surprises or confusion?
   Comments: [e.g., "No surprises. System behaved as expected."]

5. Any blockers or errors?
   Comments: [e.g., "None. Worked smoothly."]

6. Ready for Phase 7 (PDF export)? YES / NO / UNSURE
   Reason: [e.g., "Yes, but need to see how PDF looks first"]
```

### Pilot Pass Criteria (All Must Be True)

```
✓ All 5–10 test fights evaluated successfully
✓ Operator reports 4+ stars for proof clarity
✓ Operator reports 4+ stars for decision confidence
✓ Operator reports 4+ stars for gate control
✓ Zero unexpected automation or approval bypass
✓ Zero proof/data errors
✓ Zero crashes or timeouts
✓ Operator says "Yes, I'm ready for Phase 7"
```

**If All Above = TRUE**: Paid-pilot is APPROVED. Move to Phase 7A (PDF generation).

**If Any Above = FALSE**: Pause pilot. Address issues. Re-evaluate.

---

## 11. Failure & Blocked-State Handling

### Common Failure Scenarios

#### Scenario 1: Red Proof (Source Traceability Failed)

**What You See**:
```
Proof: Source Traceability | FAILED
Issue: 3 claims in Fighter A profile have no source citations
Details: Lines 12–18 lack citations
```

**What It Means**: Report was not fully sourced. Do not approve.

**What You Do**:
```
1. Click "Escalate to Button 1"
2. Reason: "Source traceability proof failed. 3 claims need citations."
3. System moves report back to Button 1 queue
4. Engineering reviews, adds sources, re-generates preview
5. You re-review (back to Step 3 of workflow)
```

#### Scenario 2: Customer-Ready Says "Not Ready"

**What You See**:
```
Customer-ready preview: customer_ready_not_ready
(One or more proofs are red/missing)
```

**What It Means**: System detected an issue. Cannot approve for customer.

**What You Do**:
```
1. Look at which proof is red (scroll up to meta-footer)
2. Click "Escalate" and explain the issue
3. Wait for remediation from Button 1
4. Re-review next iteration
```

**You Cannot Force "Ready"**: If proofs are red, you cannot override to approve. System blocks it.

#### Scenario 3: Export Gate Missing or Unclear

**What You See**:
```
Gate: operator_approval_required → NOT VISIBLE
Output path policy: ... → NOT VISIBLE
```

**What It Means**: System error. Do not proceed.

**What You Do**:
```
1. Screenshot the issue
2. Click "Report System Error"
3. Include screenshot and fight details
4. Contact engineering immediately
5. Do NOT approve this report
6. Wait for fix
```

#### Scenario 4: Proof Status Confusing or Unreadable

**What You See**:
```
Proof: [Something] | [Unclear Status] | [Unreadable Details]
```

**What It Means**: UI issue or data corruption. Do not guess.

**What You Do**:
```
1. Click "Request Clarification"
2. Screenshot the unclear area
3. Describe what's confusing (e.g., "Status text is blurry")
4. Contact pilot coordinator
5. Do NOT approve
6. Wait for clarity
```

### When to Escalate vs. When to Reject

#### Escalate to Button 1 When:
- ✓ Proofs are red (fixable by reprocessing)
- ✓ Report is missing sources (fixable by Button 1 research)
- ✓ Report is missing sections (fixable by regeneration)
- ✓ Data looks wrong but might be correctable

#### Reject (Do Not Approve) When:
- ✓ Customer-ready status is "not_ready"
- ✓ Any proof is red
- ✓ Gates are missing
- ✓ You feel unsure

### Blocked State (Cannot Proceed)

**If You See**:
```
"System Error: HTML preview failed to generate"
or
"Report generation timed out"
or
"Gate verification failed"
```

**What You Do**:
```
1. Click "Report Error"
2. Include fight details and error message
3. Contact engineering
4. This is a blocker—do NOT retry without guidance
```

---

## 12. Final Operator Verdict

### Your Role in This Pilot

You are **the gatekeeper for customer quality**.

Your decisions are **final**.

The system is here to **show you data, not make decisions for you**.

### What We're Learning from Your Feedback

1. **Are proofs clear enough?** (If not, we simplify them)
2. **Do operators feel in control?** (If not, we add transparency)
3. **Are gates working?** (If not, we lock them tighter)
4. **Are there gaps in the workflow?** (If yes, we fix them)
5. **Is anything automated that shouldn't be?** (If yes, we remove it)

### Your Final Questions

**After evaluating 5–10 fights, answer these**:

```
1. Did I ever feel like the system made a decision without my approval?
   Answer: _______________
   
2. Could I override an approval gate if I wanted to?
   Answer: _______________
   
3. Did I understand what each proof meant?
   Answer: _______________
   
4. Would I trust this report going to a paying customer?
   Answer: _______________
   
5. Am I ready for Phase 7 (PDF export and delivery)?
   Answer: _______________
   
6. Any concerns or hesitations?
   Answer: _______________
```

**If All Answers Are Positive**: Pilot is APPROVED for Phase 7.

**If Any Answer Is Negative**: Pilot is PAUSED pending fixes.

### Next Steps (Based on Your Verdict)

**If You Say "I'm Ready for Phase 7"**:
```
1. Paid-pilot closes successfully
2. Engineering begins Phase 7A (PDF generation)
3. You return as first beta tester for PDF export
4. Same approval gate workflow, now with actual PDF output
5. Cycle repeats with Phase 7B (delivery)
```

**If You Say "Not Yet"**:
```
1. Engineering addresses your concerns
2. We iterate on Phase 1–6 as needed
3. Pilot resumes with fixes in place
4. You re-evaluate
5. Repeat until ready
```

---

## Quick Reference: Approval Checklist

Print this. Keep it by your desk. Use it for every evaluation.

```
╔══════════════════════════════════════════════════════════╗
║   BUTTON 2 OPERATOR APPROVAL CHECKLIST                   ║
╚══════════════════════════════════════════════════════════╝

Fight: ________________________________   Date: __________

STEP 1: REVIEW CONTENT
  □ All sections present (title, fighters, analysis, etc.)
  □ No placeholder text or [INSERT_X] markers
  □ No data corruption or layout issues
  □ Content looks professional and complete

STEP 2: CHECK PROOFS
  □ Source Traceability: _____ (GREEN or RED?)
  □ Header/Footer/Watermark: _____ (GREEN or RED?)
  □ Chart/Scenario: _____ (GREEN or RED?)
  □ Page-Break Layout: _____ (GREEN or RED?)
  □ Typography Polish: _____ (GREEN or RED?)
  □ Overlap Check: _____ (GREEN or RED?)

  Any RED proofs? YES / NO
  If YES → DO NOT APPROVE. Escalate.

STEP 3: CHECK STATUS SIGNALS
  □ Customer-ready status: ____________________
  □ Export-eligible status: ____________________
  □ Gate text visible: operator_approval_required? YES / NO
  □ Path policy visible: server_derived_output_path_required? YES / NO

STEP 4: FINAL DECISION
  Are all conditions met?
    ✓ All proofs green
    ✓ Customer-ready status shows "recommended"
    ✓ Export-eligible status shows "pending operator approval"
    ✓ Gates are visible

  If YES to all → Click "APPROVE FOR PAYMENT SYSTEM"
  If NO to any → Click "ESCALATE" and explain reason

APPROVAL: YES / NO / ESCALATE
REASON (if escalating): ____________________________
OPERATOR NAME: __________________  DATE: __________
```

---

**Runbook Document**: `button2-paid-pilot-operator-runbook-v1`  
**Status**: DOCS-ONLY OPERATOR GUIDE  
**Timestamp**: 2026-05-18  
**Next Review**: After first pilot fight evaluation
