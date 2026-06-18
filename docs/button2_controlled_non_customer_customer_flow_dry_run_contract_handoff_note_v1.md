# Button 2 Controlled Non-Customer Customer-Flow Dry-Run Contract Handoff Note v1

Slice: button2-controlled-non-customer-customer-flow-dry-run-contract-handoff-note-v1
Date: 2026-06-18
Status: Docs-only handoff

## Purpose

Consolidate the locked Button 2 customer-flow dry-run contract scaffold and regression-hardening proof into a single handoff note before any UI/status or customer-flow expansion is considered.

This handoff note documents the decision-only dry-run boundary, the fail-closed posture, and the current boundary between the controlled non-customer proof surface and any customer-generation path.

## Current Dry-Run Contract State

- Dry-run boundary: fail-closed
- Output type: decision-only
- Customer generation: NOT ACTIVATED
- render_button2_pdf call: forbidden
- Output-path write helpers: forbidden
- Actual generation route: separate and untouched

## Locked Proof References

1. button2-controlled-non-customer-customer-flow-dry-run-contract-design-v1 / 73b7698
2. button2-controlled-non-customer-customer-flow-dry-run-contract-scaffold-v1 / 4370e50
3. button2-controlled-non-customer-customer-flow-dry-run-contract-regression-hardening-v1 / d5082bc

## Accepted Artifacts

1. docs/button2_controlled_non_customer_customer_flow_dry_run_contract_design_v1.md
2. ops/release_checks/button2-controlled-non-customer-customer-flow-dry-run-contract-design-v1/customer_flow_dry_run_contract_design_summary.json
3. operator_dashboard/button2_customer_flow_dry_run_contract_preview_v1.py
4. operator_dashboard/app.py
5. operator_dashboard/test_button2_controlled_non_customer_customer_flow_dry_run_contract_v1.py
6. operator_dashboard/test_button2_controlled_non_customer_customer_flow_dry_run_contract_hardening_v1.py

## Dry-Run Contract Details

### Contract Behavior

The dry-run contract is decision-only and fail-closed.

It may validate:

- operator-gate posture
- fight_id
- ingest_payload
- output-root readiness
- render-gate readiness

It must not perform any of the following:

- PDF render execution
- file write
- delivery
- queue/database mutation
- customer report artifact creation
- Button 1 governance changes
- Button 3 learning/calibration changes
- provider/source/network calls

### Required Decision Object Shape

The dry-run contract is designed to return a decision object containing:

- dry_run=true
- customer_generation_permitted=false
- render_execution_performed=false
- pdf_file_write_performed=false
- delivery_performed=false
- queue_database_write_performed=false
- button1_changed=false
- button3_changed=false
- decision
- blocking_reasons
- readiness_snapshot

### Blocking Reasons

The contract includes the following blocking reasons:

- customer_generation_not_authorized
- dry_run_only
- operator_gate_required
- no_customer_delivery_authority
- no_queue_database_write_authority

### Regression Hardening Coverage

The hardening proof confirmed:

- malformed request body fail-closed behavior is proven
- missing output-root readiness fail-closed behavior is proven
- no customer-generation leak is present
- the existing dry-run implementation remains untouched

## Boundary Confirmation

- no customer PDF generation
- no render execution
- no file write
- no delivery
- no queue/database mutation
- no provider execution
- no source/network calls
- no Button 1 changes
- no Button 3 changes
- no customer-report activation

## Next Allowed Step

- dry-run contract UI/status panel design
- or additional dry-run contract regression hardening if needed
- not customer generation

## Conclusion

The Button 2 dry-run contract is locked as a fail-closed, decision-only boundary check.

The scaffold and regression-hardening proof confirm that the contract can validate readiness posture without rendering, writing, delivering, or mutating anything, and the customer-generation path remains inactive.
