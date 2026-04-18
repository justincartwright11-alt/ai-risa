# Operator Runtime Runbook

## 1. Operator Purpose and Scope
This runbook guides operators in invoking, interpreting, and managing the frozen runtime execution surface. It covers only the validated, documented baseline.

## 2. Runtime Invocation Path
- Submit a canonical operator request to the operator runtime entrypoint.
- The entrypoint validates, dispatches, and returns a canonical result.

## 3. Input Validation Rules
- All required fields must be present:
  - operator_id
  - operator_action
  - operator_payload (with control_plane_summary_input and portfolio_summary_input)
- All upstreams must match the documented structure.
- No extra or speculative fields.

## 4. Outcome Interpretation Rules
- `operator_request_state: accepted` — All packs nominal, execution succeeded.
- `operator_request_state: blocked` — Blocker detected in upstream or cross-plane pack.
- `operator_request_state: failed_precondition` — Missing or malformed required input; must correct and retry.
- Always check `operator_precondition_indicator` and `operator_blocker_indicator`.

## 5. Blocked-State Handling
- Review all upstream and cross-plane pack states for blockers.
- Resolve blockers before retrying.
- Do not force or override blocked states.

## 6. Failed-Precondition Handling
- Inspect the result for missing or malformed fields.
- Correct the input structure before retrying.
- Do not retry without correction.

## 7. Retry Rules
- Retry only after correcting failed_precondition or resolving blockers.
- Never retry blindly; always address the root cause.

## 8. Escalation Rules
- If unable to resolve a blocked or failed_precondition state, escalate to the responsible engineering or operations team with the full request and result payloads.
- Provide all relevant logs and payloads for audit.

## 9. Audit/Logging Expectations
- All operator requests and results should be logged for traceability.
- No hidden mutation of input or output payloads.
- Use only canonical field names and structures.

## 10. Operator Do/Do-Not List
### Do
- Use only the documented canonical request/response structures
- Validate all inputs before invocation
- Review all result indicators before acting
- Escalate unresolved blockers or preconditions
- Keep audit logs of all invocations and results

### Do Not
- Do not mutate input payloads in place
- Do not add undocumented or speculative fields
- Do not bypass validation or acceptance gates
- Do not patch frozen layers without a new validation cycle
- Do not ignore blockers or failed_precondition results
