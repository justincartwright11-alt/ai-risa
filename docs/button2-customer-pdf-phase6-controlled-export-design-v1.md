# Button 2 Customer PDF - Phase 6 Controlled Export Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase6-controlled-export-design-v1
- Type: docs-only
- Purpose: define controlled export/download governance after Phase 5 freeze, without opening implementation or operational expansion

---

## Core Rule

Design first. No implementation in this slice.

- No export implementation yet
- No delivery automation
- No approval bypass
- No certification automation
- No uncontrolled file writes

---

## 1) Locked Phase 5 Customer-Ready Status Foundation

Phase 6 must build on the frozen Phase 5 status surface.

- Customer-ready status remains preview-only and proof-derived
- Existing gate text remains operator_approval_required
- No status-policy rewrites in this design slice

---

## 2) Export/Download Eligibility Conditions

Controlled export eligibility is policy-defined only in this slice.

Proposed eligibility prerequisites:
- customer_ready_recommended is present
- certification_readiness is ready under existing rollup metadata
- no blocking invalid/missing required proof layers
- operator initiates explicit export approval action

No implicit or automatic eligibility transitions are allowed.

---

## 3) Required Operator Approval Gates

Export remains operator-gated with explicit approval checkpoints.

Required gate sequence (design-level):
1. proof review gate
2. readiness confirmation gate
3. export approval gate

Constraints:
- no gate bypass path
- no automated approvals
- no hidden background approvals

---

## 4) Customer-Ready Status Relationship

Customer-ready status is a prerequisite signal, not an export action.

- Status may recommend readiness only
- Status cannot trigger export automatically
- Status cannot alter storage or delivery behavior

---

## 5) Server-Derived Output Path Relationship

Path selection remains server-derived and policy-controlled.

- No client-selected arbitrary write paths
- No user-provided direct filesystem targets in this design slice
- No path rewiring from current locked output model

Phase 6 design may reference server-derived path contracts only.

---

## 6) Download Surface Boundary

Controlled download surface is defined as narrow and non-automated.

- No auto-download on readiness
- No external push/send/distribution behaviors
- Download/export surface must remain bounded to approved operator action

No new public delivery channel is introduced.

---

## 7) Audit and Telemetry Requirements

Future implementation must be auditable, but this slice adds no runtime behavior.

Design requirements:
- capture approval decision context for export action
- capture readiness signal snapshot at approval time
- capture resulting export attempt outcome (success/fail)
- retain non-mutating traceability metadata association

No telemetry pipeline implementation is added in this slice.

---

## 8) Failure and Rollback Behavior

Failure behavior is fail-closed by design.

- if required proof state is missing/invalid: block export eligibility
- if approval state is missing: block export eligibility
- if write-path policy checks fail: block export eligibility

Rollback principle:
- remain in preview/readiness state with no side effects
- no partial delivery actions
- no uncontrolled writes

---

## 9) Non-Goals

This design does not:

- implement export/download code
- add delivery automation
- add certification automation
- alter approval model
- alter output paths
- introduce new file-write behavior
- alter dashboard mutation behavior

---

## 10) Future Implementation Sequence

When implementation is approved, use narrow proof-gated slices:

1. controlled export eligibility preview surface (read-only)
2. operator export gate scaffolding (no write yet)
3. server-derived path policy check integration
4. controlled write execution path under explicit approval
5. export smoke and final handoff lock

Each step must preserve:
- no approval bypass
- no delivery automation
- no certification automation
- no uncontrolled file writes
- no proof-stack or HTML data contract changes

---

## Final Verdict

Phase 6 controlled export is approved to proceed only as design-led, approval-gated, fail-closed evolution from Phase 5 readiness signaling.

This v1 design is locked with strict boundaries:
- no implementation in this slice
- no delivery automation
- no approval bypass
- no certification automation
- no output-path rewiring
- no uncontrolled file writes
