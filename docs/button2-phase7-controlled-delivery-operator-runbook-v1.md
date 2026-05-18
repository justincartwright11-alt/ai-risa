# Button 2 Phase 7 Controlled Delivery Operator Runbook

## 1. Runbook Purpose
This runbook provides operators with step-by-step instructions for executing controlled delivery in Phase 7, ensuring compliance with AI-RISA governance rules and maintaining customer-ready/draft-safe boundaries.

## 2. Source Artifacts Reviewed
- **Planning Design**: [button2-phase7-controlled-delivery-planning-design-v1.md](button2-phase7-controlled-delivery-planning-design-v1.md)
- **Planning Design Review**: [button2-phase7-controlled-delivery-planning-design-review-v1.md](button2-phase7-controlled-delivery-planning-design-review-v1.md)
- **Gap Closure Addendum**: [button2-phase7-controlled-delivery-gap-closure-addendum-v1.md](button2-phase7-controlled-delivery-gap-closure-addendum-v1.md)
- **Implementation Plan**: [button2-phase7-controlled-delivery-implementation-plan-v1.md](button2-phase7-controlled-delivery-implementation-plan-v1.md)

## 3. Operator Prerequisites Before Delivery
- Ensure all customer-ready reports are verified.
- Confirm all draft/internal reports are excluded.
- Verify customer identity and delivery targets.

## 4. Customer-Ready Report Verification Checklist
- Ensure reports meet defined quality standards.
- Verify operator approval for all customer-ready outputs.
- Confirm no draft/internal reports are included.

## 5. Draft/Internal Report Exclusion Checklist
- Verify all draft/internal reports are labeled as non-final.
- Ensure draft/internal reports are restricted to internal use.

## 6. Customer Identity and Delivery Target Confirmation
- Verify customer identity matches delivery records.
- Confirm delivery targets are accurate and up-to-date.

## 7. Operator Approval Checklist
- Review all delivery-ready outputs.
- Ensure compliance with customer-ready standards.
- Escalate if approval gates are not met.

## 8. Delivery Evidence Checklist
- Record operator approvals for all deliveries.
- Maintain detailed logs of delivery actions.
- Capture proof-of-delivery for all outputs.

## 9. Proof-of-Delivery Capture Process
- Record operator sign-offs for all deliveries.
- Verify outputs meet customer-ready standards.
- Maintain evidence of successful delivery.

## 10. Audit Record Requirements
- Record all delivery actions, approvals, and outputs.
- Maintain detailed logs for audit and rollback purposes.

## 11. Failure Handling
- Pause delivery and escalate for manual review if issues arise.
- Document all failures and corrective actions.

## 12. Manual Correction Rules
- Allow operator intervention for corrections.
- Ensure corrections are documented and approved.

## 13. Rollback/Voided-Delivery Rules
- Implement rollback procedures for failed deliveries.
- Document all voided deliveries and reasons.
- Ensure rollback actions are approved and logged.

## 14. Stop Conditions
- **Governance Violation**: Pause if governance rules are violated.
- **Approval Failure**: Pause if operator approval gates are not met.
- **Audit Failure**: Pause if audit/rollback procedures fail.

## 15. What Must Not Happen
- No automatic customer delivery without operator approval.
- No delivery of draft/internal reports as customer-ready.
- No uncontrolled database writes.
- No learning/calibration updates.

## 16. Handoff to Future Test-Contract Slice
- Ensure all operator actions are documented for test-contract validation.
- Provide detailed logs for future test-only contract expectations.

## 17. Final Runbook Verdict
- **Verdict**: Approved as a docs-only Slice A artifact, suitable to support the next test-only contract expectations slice.

---

### Safety and Governance Confirmation
- **Explicit Threshold Checks**: Confirmed.
- **Governance Compliance**: Confirmed.
- **Mandatory Pause/Escalation Rule**: Confirmed.