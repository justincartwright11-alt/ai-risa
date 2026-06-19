# Button 1 Provider Registry to Orchestrator Preview Wiring Implementation Plan v1

## 1. Purpose
Plan the safe repair for Button 1 current-week matchup discovery so approved provider registry candidates can flow into the preview orchestrator without enabling unsafe provider execution, queue/database writes, Button 2 promotion, customer PDF generation, learning, or calibration.

## 2. Source Identity
- Worktree path: C:\Users\jusin\OneDrive\Documents\Custom Office Templates
- Branch: master
- Checkpoint: 2bf816e
- Tag: button1-current-week-matchup-discovery-provider-readiness-diagnostic-v1
- Dirty state acknowledged as pre-existing and unrelated to this docs-only slice.

## 3. Reviewed Diagnostic
- docs/button1_current_week_matchup_discovery_provider_readiness_diagnostic_v1.md

## 4. Planning Conclusion
- Repair may proceed to implementation planning only.
- No code implementation is approved by this document.
- No provider enablement is approved.
- No provider execution is approved.
- No network calls are approved.
- No queue/database/customer-PDF/learning/calibration writes are approved.
- No Button 2 promotion is approved.
- No auto-save is approved.

## 5. Root-Cause Chain
- Dashboard shows no current-week source-backed rows.
- Provider registry contains ufc_official_events and one_fc_official_events.
- Enabled candidates are 0 / 2.
- Runtime preview passes empty provider registry into orchestrator.
- Execution gate denies because provider is not enabled and operator approval is missing.
- Stale/unavailable feed is a downstream symptom.
- Parser failure is not the primary evidence-backed blocker.

## 6. Affected File Map
- operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py
- operator_dashboard/button1_approved_provider_config_validator_v1.py
- operator_dashboard/button1_approved_provider_config_registration_v1.py
- operator_dashboard/button1_config_registration_to_orchestrator_registry_adapter_v1.py
- operator_dashboard/button1_live_source_provider_orchestrator_v1.py
- operator_dashboard/button1_provider_adapter_execution_gate_v1.py
- ops/approved_sources/button1_live_provider_registry.json
- operator_dashboard/templates/index.html
- operator_dashboard/app.py

## 7. Proposed Future Implementation Scope
- Add or adjust preview-only wiring so registry adapter candidates can be passed into the Button 1 live-source orchestrator preview.
- Preserve provider execution deny-by-default.
- Preserve operator approval requirement.
- Preserve no-write behavior.
- Preserve source-backed preview-only rows.
- Preserve queue-save blocking unless provenance and operator gate requirements are satisfied.
- Do not enable real provider execution in the first repair slice unless separately gated.

## 8. Proposed Future File Scope
- Likely operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py
- Likely tests for Button 1 provider-registry-to-orchestrator preview wiring
- No app.py changes unless later review proves unavoidable
- No template changes unless later review proves unavoidable
- No registry JSON changes in first implementation slice
- No Button 2 files
- No provider execution adapter activation files
- No queue/database/customer-PDF/learning/calibration files

## 9. Proposed Future Interface and Logic Changes
- Load provider registry candidates through existing registration and adapter path.
- Pass valid registry candidates into orchestrator preview instead of hardcoded empty list.
- Keep provider execution disabled unless explicit operator approval and provider-enabled conditions are satisfied.
- Surface candidate and provider diagnostics clearly.
- Preserve fail-closed behavior when enabled candidates remain 0.
- Preserve fail-closed behavior when operator approval is missing.
- Preserve fail-closed behavior when source rows are not provenance-backed.

## 10. Required Future Test Cases
- Empty provider registry returns no_approved_live_source_provider_configured.
- Registry with both providers disabled returns no_enabled_provider.
- Disabled ufc_official_events remains denied.
- Enabled provider without operator approval remains denied.
- Operator approval missing returns execution_gate_operator_approval_missing.
- Provider not enabled returns execution_gate_provider_not_enabled.
- Registry candidates flow into orchestrator preview when present.
- Orchestrator preview does not write queue or database.
- Button 2 promotion remains false.
- Customer PDF generation remains false.
- Learning and calibration writes remain false.
- Source-backed preview rows remain blocked if provenance is missing.
- Stale and unavailable feed fails closed.
- Parser failure is reported separately if it occurs.

## 11. Safe Repair Invariants
- All write flags remain false.
- Provider execution remains deny-by-default.
- Operator approval remains required.
- No scraping bypass.
- No queue save.
- No database write.
- No report generation.
- No Button 2 activation.
- No learning or calibration.
- No customer-facing delivery.

## 12. Implementation Readiness Prerequisites
- Design review
- File-scope review
- Test-plan review
- Implementation readiness gate
- Narrow implementation slice only after gate approval

## 13. Explicit Blocked Scope
- No implementation in this slice.
- No provider enablement.
- No network calls.
- No scraping.
- No app.py change.
- No template change.
- No registry JSON change.
- No queue/database writes.
- No Button 2 promotion.
- No customer PDF or report generation.
- No learning or calibration writes.
- No worktree cleanup.
- No staging of pre-existing dirty files.

## 14. Final Plan Verdict
BUTTON1_PROVIDER_REGISTRY_TO_ORCHESTRATOR_PREVIEW_WIRING_IMPLEMENTATION_PLAN_READY_FOR_REVIEW_ONLY

## 15. Safe Next Action
Docs-only implementation plan review and file-scope gate for Button 1 provider-registry-to-orchestrator preview wiring.
