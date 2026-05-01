# AI-RISA Premium Report Factory - Button 3 Result Comparison Learning Design v1

Document Type: Product and Workflow Design (Docs-Only)
Date: 2026-05-01
Slice Name: ai-risa-premium-report-factory-button3-result-comparison-learning-design-v1
Status: Design Draft for Lock

---

## 1. Purpose

Define Button 3 product design for:
Find Results and Improve Accuracy.

Target workflow:
automatic official-source result search
-> manual result input
-> candidate result review window
-> operator approval before applying result
-> compare real result vs analysis/report
-> accuracy views and governed learning proposal
-> approved calibration update only after operator approval.

This is a design-only slice.
No implementation, no endpoint changes, and no dashboard changes are authorized in this slice.

---

## 2. Product Context

Current baseline capabilities:
1. Button 1: Find and Build Fight Queue (built and archived)
2. Button 2: Generate Premium PDF Reports (built and archived)
3. Button 3: not opened before this design

Button 3 is defined as a governed post-report feedback loop:
- discover or enter actual results
- verify and approve result application
- compare prediction/report outputs to actual outcomes
- compute multi-level accuracy metrics
- prepare learning/calibration updates only under explicit approval.

---

## 3. Governance Model

Core policy for Button 3:
- Automatic official-source search is allowed.
- Manual result input is allowed.
- Any permanent mutation (result apply, scoring write, calibration/learning apply) requires explicit operator approval.
- No automatic write path is allowed.

Hard rules for this design slice:
- Docs-only
- No implementation
- No endpoint changes
- No dashboard changes
- No learning/calibration code
- No automatic writes

---

## 4. Scope Inclusions

### 4.1 Automatic Official-Source Result Search

Button 3 supports controlled automatic search for candidate official results:
- official event pages
- official result posts
- trusted official-source result feeds

Expected output:
- candidate result objects
- source references
- confidence tier/classification
- parse/identity warnings

### 4.2 Manual Result Input

Operator may enter result manually when automatic search is incomplete or uncertain.

Manual fields:
- matchup identity
- winning fighter
- method
- round/time (if available)
- source note/reference
- operator note

### 4.3 Candidate Result Review Window

Review window must present, per candidate:
- selected matchup identity
- candidate actual result values
- source reference and confidence indicators
- matching/identity checks
- conflict or ambiguity flags

Operator controls:
- select one candidate
- reject candidate(s)
- request manual correction
- proceed to approval gate

### 4.4 Approval Before Apply

Approval gate requirements:
- explicit operator approval control before apply
- apply action disabled until approval granted
- approval metadata captured for audit
- no background/silent apply behavior

### 4.5 Comparison Against Analysis/Report

After approved apply, compare actual result to prediction/report outputs:
- winner hit/miss
- method hit/miss (when available)
- round/timing closeness (when available)
- segment-level outcome rollups

### 4.6 Accuracy Views Required

Button 3 design must include these accuracy outputs:
1. single fighter accuracy
2. matchup accuracy
3. event-card accuracy
4. segment accuracy
5. total AI-RISA accuracy

Metric output design principles:
- deterministic definitions
- transparent denominators
- unresolved/partial records clearly separated from scored records

### 4.7 Governed Learning/Calibration Update

Learning/calibration flow in Button 3 is proposal-first:
- derive suggested calibration update from approved comparison outcomes
- present proposal summary and projected effect
- require explicit operator approval before apply

No design allowance for automatic calibration apply.

---

## 5. Detailed Workflow

Step 1 - Select target matchup/report context
- Operator identifies scoped target for result resolution.

Step 2 - Gather result candidates
- Automatic official-source search runs.
- Manual result input remains available.

Step 3 - Review candidates
- Candidate result review window shows confidence and conflicts.

Step 4 - Choose candidate or manual entry
- Operator selects final result candidate.

Step 5 - Approval gate for result apply
- Explicit approval required.
- Apply remains disabled without approval.

Step 6 - Apply approved result
- Persist approved result under governed write boundary.

Step 7 - Compare vs prediction/report
- Generate comparison outcomes and scoring statuses.

Step 8 - Compute accuracy layers
- Produce fighter, matchup, event-card, segment, and total accuracy views.

Step 9 - Prepare learning/calibration proposal
- Build proposal from approved evidence only.

Step 10 - Approval gate for calibration update
- Explicit approval required before any calibration apply.

---

## 6. UI-Level Data Contract Design (Design Only)

### 6.1 Candidate Result Record

Fields:
- candidate_result_id
- matchup_key
- fighter_a
- fighter_b
- actual_winner
- actual_method
- actual_round
- actual_time
- source_reference
- source_confidence_tier
- identity_match_status
- parse_status
- warnings

### 6.2 Approved Apply Envelope

Fields:
- approval_required
- approval_granted
- operator_id_or_label
- approved_at_utc
- selected_candidate_result_id
- apply_status
- write_audit_reference
- errors

### 6.3 Comparison Outcome Record

Fields:
- comparison_id
- matchup_key
- winner_hit
- method_hit
- round_alignment
- confidence_alignment
- scored_status
- unresolved_reason

### 6.4 Accuracy Summary Contract

Fields:
- fighter_accuracy
- matchup_accuracy
- event_card_accuracy
- segment_accuracy
- total_ai_risa_accuracy
- denominator_summary
- unresolved_count
- generated_at_utc

### 6.5 Calibration Proposal Contract

Fields:
- proposal_id
- proposal_reason
- evidence_window
- projected_impact
- approval_required
- approval_granted
- apply_status
- audit_reference

---

## 7. Guardrails and Non-Goals

Guardrails:
1. Restrict automatic search to official-source categories.
2. Keep candidate-confidence and conflict information visible.
3. Require explicit approval before any permanent mutation.
4. Keep comparison and accuracy computations auditable.
5. Keep calibration/learning updates proposal-first and approval-gated.

Non-goals in this design slice:
- implementation work
- endpoint additions/modifications
- dashboard UI modifications
- automatic mutation paths
- unsupervised learning/calibration application

---

## 8. Risks and Controls

Primary risks:
1. Source ambiguity and false positives in result search.
2. Identity mismatch across similarly named fighters/matchups.
3. Approval bypass risk in edge flows.
4. Metric misinterpretation from unresolved records.
5. Scope creep into non-Button-3 domains.

Controls:
1. Candidate review window with explicit confidence and conflict cues.
2. Identity checks and manual correction path before approval.
3. Hard approval gates before apply operations.
4. Deterministic denominator and unresolved-status reporting.
5. Strict boundary statements and slice-based governance.

---

## 9. Success Criteria for Future Implementation

Button 3 implementation is complete only when:
1. Automatic official-source result search is available with candidate outputs.
2. Manual result input path is available.
3. Candidate result review window supports safe operator selection.
4. Result apply requires explicit operator approval.
5. Comparison to prediction/report is produced per approved result.
6. Accuracy is available at fighter, matchup, event-card, segment, and total levels.
7. Learning/calibration update path is proposal-first and approval-gated.
8. No automatic writes are introduced.
9. No out-of-scope behavior is introduced.

---

## 10. Implementation Readiness Statement

This design establishes the Button 3 product boundary and governance constraints.
Implementation remains blocked until a separate Button 3 design-review slice is opened and locked.
