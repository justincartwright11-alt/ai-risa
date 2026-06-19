# Button 1 Provider Registry to Orchestrator Preview Wiring Plan Review and File Scope Gate v1

## 1. Purpose
Review the Button 1 provider-registry-to-orchestrator preview wiring implementation plan and define the allowed future implementation file scope before any code repair.

## 2. Source Identity
- Worktree path: C:\Users\jusin\OneDrive\Documents\Custom Office Templates
- Branch: master
- Checkpoint: ba3f1b0
- Tag: button1-provider-registry-to-orchestrator-preview-wiring-implementation-plan-v1
- Dirty state acknowledged as pre-existing and unrelated.

## 3. Reviewed Inputs
- docs/button1_current_week_matchup_discovery_provider_readiness_diagnostic_v1.md
- docs/button1_provider_registry_to_orchestrator_preview_wiring_implementation_plan_v1.md

## 4. Review Conclusion
- Implementation plan is structurally acceptable for file-scope gating.
- Provider-registry-to-orchestrator preview wiring may proceed to implementation readiness only.
- No implementation is approved by this review.
- No provider enablement is approved.
- No provider execution is approved.
- No network calls are approved.
- No queue/database/customer-PDF/learning/calibration writes are approved.
- No Button 2 promotion is approved.
- No auto-save is approved.

## 5. Review Matrix
| Review Item | Status | Notes |
|---|---|---|
| Root cause identified | PASS | Locked in prior diagnostic. |
| Provider registry candidates identified | PASS | ufc_official_events and one_fc_official_events. |
| Disabled provider state identified | PASS | Enabled count remains 0 / 2. |
| Runtime empty-registry path identified | PASS | Preview runtime hardcoded empty provider registry path documented. |
| Operator gate denial identified | PASS | Missing approval and provider-not-enabled denial codes captured. |
| Stale/unavailable feed classified as downstream symptom | PASS | Treated as effect, not primary blocker. |
| Parser failure not treated as primary cause | PASS | Explicitly non-primary per evidence chain. |
| Safe repair boundary defined | PASS | Locked no-write/no-promotion/no-execution boundary. |
| Write paths blocked | PASS | Queue/database/customer outputs blocked. |
| Provider execution deny-by-default preserved | PASS | Preserved by plan and review gate. |
| Operator approval requirement preserved | PASS | Required and preserved. |
| No Button 2 promotion preserved | PASS | Explicitly blocked in scope. |
| No auto-save preserved | PASS | Explicitly blocked in scope. |
| Proposed file scope defined | PASS | Narrow scope defined below. |
| Required future tests defined | PASS | Required tests retained and extended. |
| Blocked scope defined | PASS | Explicit blocked scope listed below. |

## 6. Approved Future Implementation File Scope
- operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py
- New test file for Button 1 provider-registry-to-orchestrator preview wiring; exact filename to be proposed in the implementation readiness gate.

## 7. Conditionally Allowed Only if Later Review Proves Unavoidable
- No app.py change by default.
- No template change by default.
- No provider registry JSON change by default.

## 8. Explicitly Blocked Future First-Slice File Scope
- operator_dashboard/app.py
- operator_dashboard/templates/index.html
- ops/approved_sources/button1_live_provider_registry.json
- Button 2 files
- Provider execution adapter activation files
- Queue/database files
- Customer PDF files
- Learning/calibration files
- Unrelated docs/root files
- Pre-existing dirty files

## 9. Required Future Implementation Behavior
- Load provider registry candidates through existing registration/adapter path.
- Pass valid registry candidates into live-source orchestrator preview instead of hardcoded empty list.
- Keep provider execution disabled unless separately gated.
- Keep operator approval required.
- Keep all write flags false.
- Surface current provider candidate diagnostics.
- Preserve fail-closed behavior when enabled candidates remain 0.
- Preserve fail-closed behavior when operator approval is missing.
- Preserve fail-closed behavior when provenance is missing.
- Do not auto-save or promote to Button 2.

## 10. Required Future Test Cases
- Empty provider registry returns no_approved_live_source_provider_configured.
- Registry with both providers disabled returns no_enabled_provider.
- Disabled ufc_official_events remains denied.
- Enabled provider without operator approval remains denied.
- Operator approval missing returns execution_gate_operator_approval_missing.
- Provider not enabled returns execution_gate_provider_not_enabled.
- Registry candidates flow into orchestrator preview when present.
- Orchestrator preview does not write queue/database.
- Button 2 promotion remains false.
- Customer PDF generation remains false.
- Learning/calibration writes remain false.
- Source-backed preview rows remain blocked if provenance is missing.
- Stale/unavailable feed fails closed.
- Parser failure is reported separately if it occurs.

## 11. Implementation Readiness Prerequisites
- Implementation readiness gate
- Exact test filename
- Exact staged-file allowlist
- Rollback/abort policy
- Local pytest command
- Staged-set guard
- Dirty-worktree handling policy

## 12. Rollback and Abort Policy
- Abort if implementation touches app.py.
- Abort if implementation touches templates.
- Abort if implementation touches registry JSON.
- Abort if implementation touches Button 2 files.
- Abort if implementation touches provider execution adapter activation files.
- Abort if implementation touches queue/database/customer-PDF/learning/calibration paths.
- Abort if provider execution occurs.
- Abort if network call occurs.
- Abort if queue/database/customer-PDF/learning/calibration write occurs.
- Abort if pre-existing dirty files are staged.
- Abort if pytest fails.

## 13. Explicit Blocked Scope
- No implementation in this slice.
- No provider enablement.
- No provider execution.
- No network calls.
- No scraping.
- No app.py change.
- No template change.
- No registry JSON change.
- No queue/database writes.
- No Button 2 promotion.
- No customer PDF/report generation.
- No learning/calibration writes.
- No worktree cleanup.
- No staging of pre-existing dirty files.

## 14. Final Gate Verdict
BUTTON1_PROVIDER_REGISTRY_TO_ORCHESTRATOR_PREVIEW_WIRING_PLAN_REVIEW_APPROVED_FOR_IMPLEMENTATION_READINESS_GATE_ONLY

## 15. Safe Next Action
Docs-only implementation readiness gate for Button 1 provider-registry-to-orchestrator preview wiring.
