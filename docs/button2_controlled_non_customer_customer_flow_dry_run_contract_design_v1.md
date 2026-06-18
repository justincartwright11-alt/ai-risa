# Button 2 Controlled Non-Customer Customer-Flow Dry-Run Contract Design v1

Slice: button2-controlled-non-customer-customer-flow-dry-run-contract-design-v1
Date: 2026-06-18
Status: Docs-only design

## Purpose

Design a dry-run contract for safely testing the Button 2 customer-flow boundary without rendering or writing customer PDFs.

This dry-run contract is read-only by design. It validates customer-flow preconditions, returns a decision object, and stops before any customer-generation action can occur.

## Core Rule

Design first. No implementation in this slice.

- No PDF render execution
- No file write
- No delivery
- No queue/database mutation
- No customer report artifact
- No Button 1 provider changes
- No Button 3 learning/calibration changes
- No provider/source/network calls

## 1) Dry-Run Purpose

The dry-run exists to validate customer-flow preconditions without rendering or writing customer PDFs.

Dry-run outputs only a decision object and never advances into customer report generation.

## 2) Dry-Run Allowed Behavior

The dry-run contract may:

- accept a controlled non-customer payload
- validate required fields
- validate operator-gate posture
- validate output-root readiness
- validate render-gate readiness flags
- produce a dry-run decision object only

## 3) Dry-Run Forbidden Behavior

The dry-run contract must never:

- execute PDF rendering
- write files
- deliver reports
- mutate queue or database state
- create any customer report artifact
- alter Button 1 governance
- alter Button 3 learning/calibration
- call providers, sources, or network services

## 4) Required Dry-Run Output Fields

The dry-run decision object must include:

- `dry_run=true`
- `customer_generation_permitted=false`
- `render_execution_performed=false`
- `pdf_file_write_performed=false`
- `delivery_performed=false`
- `queue_database_write_performed=false`
- `button1_changed=false`
- `button3_changed=false`
- `decision`
- `blocking_reasons`
- `readiness_snapshot`

## 5) Blocking Reasons

The contract must support the following blocking reasons:

- `customer_generation_not_authorized`
- `dry_run_only`
- `operator_gate_required`
- `no_customer_delivery_authority`
- `no_queue_database_write_authority`

Blocking reasons are informational only; they do not enable any write or render path.

## 6) Readiness Snapshot

The readiness snapshot must summarize the preconditions that would be checked before customer generation, including:

- operator approval posture
- fight or matchup identifier presence
- ingest payload presence and shape
- report-context readiness posture
- render-gate readiness flags
- output-root readiness posture

The snapshot is diagnostic only and must not imply generation permission.

## 7) Future Implementation Constraints

Any future dry-run implementation must obey these constraints:

- dry-run route or function must be separate from the actual generation route
- dry-run must fail closed
- dry-run must never call `render_button2_pdf`
- dry-run must never call output-path write helpers
- dry-run must be regression tested before any customer-flow activation

## 8) Relationship to the Locked Boundary Diagnosis

The locked boundary diagnosis established where the controlled proof chain ends and where customer generation begins.

This dry-run contract sits immediately before customer generation, but it still remains outside customer activation because it is read-only and decision-only.

Dry-run may confirm whether the customer-generation preconditions are present, but it must not fulfill them by invoking render, file write, or delivery.

## 9) Next Allowed Slice

- dry-run contract scaffold only
- not customer generation

## Conclusion

The Button 2 customer-flow dry-run contract is defined as a fail-closed, decision-only boundary check.

It validates readiness posture without rendering, writing, delivering, or mutating anything, and it must remain separate from actual customer-generation routes.
