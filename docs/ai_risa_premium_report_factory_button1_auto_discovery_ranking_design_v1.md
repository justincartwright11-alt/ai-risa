# AI-RISA Premium Report Factory - Button 1 Auto Discovery Ranking Design v1

Document Type: Product and Workflow Design (Docs-Only)
Date: 2026-05-01
Slice Name: ai-risa-premium-report-factory-button1-auto-discovery-ranking-design-v1
Status: Design Draft for Lock

---

## 1. Purpose

Design Button 1 of the main product surface:
Find and Build Fight Queue.

Target workflow:
Automatic official-source web discovery + manual input
-> extract matchups
-> analyze and rank report readiness
-> review window
-> operator approval
-> save to database and queue

This is a design-only slice. No implementation in this slice.

---

## 2. Product Context

Main dashboard remains a three-button surface:
1. Find and Build Fight Queue (this slice)
2. Generate Premium PDF Reports (already archived and closed)
3. Find Results and Improve Accuracy (future)

Advanced Dashboard remains the internal tools boundary.

---

## 3. Governance Model for Button 1

Core rule:
AI-RISA may search, collect, parse, and rank automatically.
Permanent database and queue writes require explicit operator approval.

Button 1 governance mapping:
- Auto discovery: allowed without approval
- Manual input parsing and extraction: allowed without approval
- Readiness scoring and ranking: allowed without approval
- Review display: allowed without approval
- Save to queue and database: approval required
- Audit trail for each approval and save action: required

No hidden automatic save is allowed.

---

## 4. Scope Inclusions

### 4.1 Discovery Inputs

Automatic official-source discovery:
- Official promoter and event pages
- Official schedule feeds and event listings
- Official or trusted event-card announcements

Manual input options:
- Paste raw event-card text
- Type freeform matchup lines
- Paste structured card snippets

### 4.2 Extraction

Extract canonical matchup records from discovered and manual input:
- Fighter A
- Fighter B
- Event metadata when available
- Card order when available
- Source reference

### 4.3 Readiness Analysis and Ranking

Each extracted matchup receives a readiness score and rank:
- Data completeness signals
- Name confidence and parse confidence
- Event-date availability
- Source quality and reference presence
- Required-field coverage for report generation

Readiness categories:
- Ready
- Partial
- Needs review

### 4.4 Review Window

Operator review surface includes:
- Matchup list table
- Extraction confidence cues
- Readiness score and readiness bucket
- Select one, many, or all
- Reject or deselect rows
- Optional inline correction fields for fighter names

### 4.5 Approval and Save

Operator approval gate before write:
- Explicit approval checkbox or equivalent control
- Save action disabled until approval granted
- Save selected rows only
- Persist to queue and database through existing approved-save boundary

Post-save behavior:
- Show accepted count and rejected count
- Show reasons for rejected rows
- Refresh upcoming queue view

---

## 5. Detailed Workflow

Step 1 - Gather input
- Auto discovery runs for approved official-source targets
- Manual input accepted in parallel

Step 2 - Parse and extract
- Build normalized matchup preview rows
- Attach parse warnings and errors

Step 3 - Score readiness
- Compute readiness score per row
- Assign readiness class and rank order

Step 4 - Present review window
- Display rows and confidence details
- Operator selects one, many, or all

Step 5 - Approval gate
- Operator grants approval for save
- Save action enabled only when approval is present

Step 6 - Save selected rows
- Write approved rows to queue and database
- Return save summary and row-level outcomes

Step 7 - Display save outcomes
- Accepted and rejected summaries
- Queue refresh for immediate visibility

---

## 6. Data Contract Design (UI-Level)

Button 1 preview row fields:
- temporary_matchup_id
- fighter_a
- fighter_b
- event_name
- event_date
- promotion
- location
- source_reference
- parse_status
- parse_notes
- readiness_score
- readiness_bucket
- confidence_score

Button 1 save outcome fields:
- accepted_count
- rejected_count
- saved_matchups
- rejected_matchups
- queue_summary
- warnings
- errors

Notes:
- This design reuses existing queue-save boundaries where possible.
- New fields, if introduced later, must remain backward compatible.

---

## 7. UI Surface Design for Main Dashboard

Button label:
Find and Build Fight Queue

Primary panel blocks:
1. Discovery and Manual Input
2. Matchup Extraction Preview
3. Readiness Ranking Table
4. Approval and Save Controls
5. Save Outcome and Queue Snapshot

Essential controls:
- Run discovery
- Parse preview
- Select all
- Row checkboxes
- Approval checkbox
- Save selected

Essential states:
- Empty state with guidance
- Loading state for discovery and parsing
- Validation state for required approval
- Success and error states for save results

---

## 8. Non-Goals for This Slice

This slice does not include implementation.

This slice does not include:
- Button 2 changes
- Button 3 or Phase 4 behavior
- Result lookup
- Learning or calibration updates
- Billing automation
- Global-ledger behavior changes
- Hidden automatic writes

---

## 9. Risks and Guardrails

Primary risks:
1. Non-official-source ingestion drift
2. False-positive extraction rows
3. Approval-gate bypass in UI edge paths
4. Scope creep into Button 2 or Button 3 domains

Guardrails:
1. Restrict discovery to approved official-source categories
2. Keep parse warnings visible and auditable
3. Block save unless explicit operator approval is present
4. Preserve queue-save contract and audit logging
5. Keep this slice design-only until design review locks

---

## 10. Success Criteria for Future Implementation

Implementation of Button 1 is complete only when:
1. Official-source discovery can be triggered safely
2. Manual input parsing works with preview rows
3. Matchups are extracted with confidence indicators
4. Readiness score and ranking are displayed for each row
5. Operator can select one, many, or all rows
6. Save is blocked without approval
7. Approved save persists selected rows only
8. Save results show accepted and rejected outcomes
9. Queue refresh reflects new saved rows
10. No out-of-scope behavior is introduced

---

## 11. Implementation Readiness Statement

This design defines the boundary and expected workflow for Button 1.
Implementation remains blocked until the design-review slice is created and locked.

Next required slice:
ai-risa-premium-report-factory-button1-auto-discovery-ranking-design-review-v1

---

## 12. Design Verdict

Verdict: Ready for Design Review

This document is approved as a docs-only design boundary for Button 1 auto discovery and readiness ranking workflow.
No implementation is authorized by this design document alone.

End of design document.
