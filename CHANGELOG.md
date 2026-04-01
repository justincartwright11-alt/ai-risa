# Changelog

## v1.1-ops-visibility
- added latest-run failure detection based on canonical run history and stage summaries
- added daily health summary artifacts in JSON and Markdown
- added scheduler wrappers for ops visibility jobs
- no core pipeline behavior changes

## v1.1-ops-visibility-slice-2
- added shared read-only aggregation module for daily, weekly, and operator summary artifacts
- added weekly health rollup artifacts in JSON and Markdown
- added lightweight operator summary artifacts in JSON and Markdown
- added weekly rollup scheduler wrapper and task registration
- updated daily/weekly wrappers to refresh operator summary artifact
- no core pipeline behavior changes

## v1.1-ops-visibility-slice-3
- added scheduler verification script with pass/warn/fail status model and required task coverage
- added optional transition-based notification hooks with local-first sinks and persisted state
- added daily/weekly operator checklist artifact generation
- updated alert/daily/weekly wrappers to refresh notification, verification, and checklist outputs
- updated ops visibility docs for slice-3 operational assurance workflow
- no core pipeline behavior changes

## v1.2-source-hardening-slice-1
- validated BoxingScene adapter as live and bounded (timeout + capped retry + explicit failure diagnostics)
- hardened JSON-LD location normalization when address fields are partially combined (e.g. region includes country)
- kept adapter structure intact; no ingestion schema changes

## v1.2-source-hardening-slice-2
- hardened dependency resolver fighter extraction for canonical and alternate bout shapes (`fighter_1/2`, `fighters[]`, matchup text)
- added explicit unresolved diagnostics for missing or partial fighter identity resolution
- preserved existing resolver/queue summary schema and downstream stage contracts

## v1.2-source-hardening-slice-3
- hardened queue builder handling for unresolved and partial enrichment states from resolver outputs
- added explicit queue-build diagnostics for unresolved fighter identity, partial identity, and unresolved matchup mapping
- prevented insufficiently enriched rows from silent queue promotion while preserving queue row compatibility for valid fights

## v1.2-source-hardening-slice-4
- standardized unresolved/partial reason-code wording across resolver and queue-build warning surfaces
- added coherent insufficient-enrichment count/reporting in resolver summary
- added queue-build reason-code tally for operator visibility while preserving existing summary contracts

## v1.2-source-hardening-slice-5
- hardened full-pipeline summary propagation to surface resolver and queue-build unresolved/partial/insufficient-enrichment diagnostics at top level
- added additive operator-facing enrichment diagnostic warnings and count rollups in full-pipeline summary output
- preserved canonical stage contracts and run behavior (no scheduler or execution semantic changes)

## v1.2-source-hardening-stabilization-defects
- fixed schedule normalization crash path when upstream bout entries are strings rather than dict objects
- fixed queue-run non-zero failures caused by Windows-invalid prediction output filenames derived from unsanitized IDs
- kept stabilization scope narrow (no schema or scheduler changes)

## v1.3-reporting-quality-slice-1
- improved top-level report clarity with additive analysis coverage and skipped/exclusion blocks in full-pipeline and batch summaries
- added clearer operator interpretation notes for non-fatal warning runs versus hard-failure runs
- preserved canonical schemas and run behavior (reporting-layer additive changes only)

## v1.3-reporting-quality-slice-2
- improved warning readability with explicit operator-facing messages in full-pipeline and batch summaries
- added additive warning-readability classification blocks to separate informational/non-fatal warnings from action-needed conditions
- clarified dry-run versus normal-run interpretation without changing run behavior or canonical schemas

## v1.3-reporting-quality-slice-3
- improved human-readable summary presentation with ordered sections: executive summary, coverage snapshot, exclusions snapshot, warning interpretation, and recommended action
- surfaced markdown-ready operator summary blocks in full-pipeline and batch summary details without altering existing computed metrics
- preserved canonical schemas and run behavior (additive presentation-only enhancements)

## v1.4-operator-dashboard-slice-1
- added a minimal read-only operator dashboard artifact generator that consumes existing summary outputs and reporting-quality blocks
- added operator dashboard artifacts in JSON and Markdown at ops/dashboard for fast latest-run operational visibility
- preserved pipeline behavior and canonical schemas (dashboard/read-layer only)

## v1.4-operator-dashboard-cleanup
- fixed dashboard source-summary metadata checks to use repo-root-qualified paths for correct existence and timestamp reporting
- reclassified ops/dashboard/operator_dashboard.json and ops/dashboard/operator_dashboard.md as runtime-generated artifacts
- added ignore rules and removed dashboard artifact outputs from Git tracking while keeping the generator script tracked

## v1.4-operator-dashboard-slice-2
- added per-source freshness indicators (fresh/stale/stale-critical/missing/unreadable) to improve staleness scanning speed
- added prioritized recommended actions so the most important operator action appears first
- added compact source-summary health and run-to-run change snapshot blocks derived read-only from existing summaries and run history
- preserved pipeline behavior and canonical schemas (dashboard usability/read-layer only)

## v1.5-operator-workflows-slice-1
- added a read-only operator action queue generator derived from existing dashboard and reporting signals
- prioritized queue items by severity and freshness with suggested handling states for operator follow-up
- added runtime-generated JSON and Markdown action-queue artifacts without changing pipeline logic or scheduler behavior

## v1.5-operator-workflows-slice-2
- added a separate operator workflow state overlay with local statuses such as new, acknowledged, deferred, and resolved
- added a merged operator worklist artifact that overlays local operator state on the read-only derived action queue
- preserved queue and dashboard sources as read-only inputs with no pipeline, scheduler, or canonical schema changes

## v1.6-operator-automation-slice-1
- added a read-only automation and escalation queue derived from the operator worklist
- flagged escalation, reminder, priority-boost, and handoff recommendations without mutating workflow state automatically
- added runtime-generated JSON and Markdown automation queue artifacts without changing pipeline or scheduler behavior

## v1.7-model-calibration-slice-1
- added a read-only model calibration report generator that analyzes resolved prediction-vs-actual history and pending unevaluable queue rows
- added calibration diagnostics for evaluated accuracy, confidence buckets, over/underconfidence indicators, and recurring miss-pattern summaries
- added runtime-generated calibration report artifacts in JSON and Markdown with recommended follow-up actions, without changing pipeline or scheduler behavior

## v1.8-calibration-actions-slice-1
- added a read-only calibration action queue generator derived from the model calibration report, reconciliation history, and pending prediction backlog
- added prioritized action categories for overconfidence review, sparse-confidence bucket review, recurring miss-pattern investigation, and data-gap cleanup
- added runtime-generated calibration action queue artifacts in JSON and Markdown without mutating model behavior or changing pipeline/scheduler logic

## v1.9-calibration-interventions-slice-1
- added a read-only calibration intervention plan generator derived from calibration diagnostics, calibration action queue priorities, and reconciliation signals
- added proposed intervention types for confidence-threshold review, confidence-bucket coverage review, recurring miss-family investigation, data-gap cleanup prerequisites, and candidate weighting/rule-review targets
- added runtime-generated calibration intervention plan artifacts in JSON and Markdown without mutating model behavior or changing pipeline/scheduler logic

## v2.0-controlled-model-adjustments-slice-1
- added a read-only controlled model-adjustment proposal generator derived from calibration reports, calibration action queues, and intervention plans
- added approval-gated proposal packages for confidence-threshold review, confidence-bucket coverage review, miss-family weighting review, rule-review targets, and data-gap prerequisite gates
- added runtime-generated controlled model-adjustment proposal artifacts in JSON and Markdown without mutating model behavior or changing pipeline/scheduler logic

## v2.1-adjustment-approval-ledger-slice-1
- added a read-only model-adjustment approval ledger generator derived from controlled model-adjustment proposal artifacts
- added explicit control-state defaults for pending review, undecided outcome, blocked application readiness, reviewer-role requirements, and validation gating metadata
- added runtime-generated approval-ledger artifacts in JSON and Markdown without model mutation, auto-approval, or pipeline/scheduler changes

## v2.2-adjustment-validation-manifests-slice-1
- added a read-only model-adjustment validation-manifest generator derived from controlled model-adjustment proposals and approval-ledger control state
- added validation-manifest defaults for pending validation, simulation-only scope, required test classes/metrics, pass criteria, rollback requirements, and blocked application readiness
- added runtime-generated validation-manifest artifacts in JSON and Markdown without model mutation, execution promotion, or pipeline/scheduler changes

## v2.3-adjustment-application-gates-slice-1
- added a read-only model-adjustment application-gate generator derived from proposals, approval-ledger state, and validation-manifest state
- added conservative gate classification output (`blocked`, `conditionally_eligible`, `eligible_for_controlled_application`) with gate decisions, reasons, pre-application checks, and operator-role requirements
- added runtime-generated application-gate artifacts in JSON and Markdown without model mutation, auto-application, or pipeline/scheduler changes

## v2.4-controlled-application-packets-slice-1
- added a read-only controlled application packet generator derived from proposals, approval-ledger state, validation-manifest state, and application-gate state
- added operator-ready packet fields for packet status, manual-review-only mode, planned change scope, required sources/backups/checks, rollback plan, and conservative execution readiness
- added runtime-generated controlled application packet artifacts in JSON and Markdown without model mutation, auto-application, or pipeline/scheduler changes

## v2.5-controlled-application-dry-runs-slice-1
- added a read-only controlled application dry-run generator derived from proposals, approval-ledger state, validation manifests, application gates, and application packets
- added rehearsal-layer fields for ordered dry-run steps, checkpoint sequence, preconditions, abort conditions, expected observations, operator role, and conservative dry-run readiness
- added runtime-generated controlled application dry-run artifacts in JSON and Markdown without model mutation, auto-application, or pipeline/scheduler changes

## v2.6-controlled-application-authorizations-slice-1
- added a read-only controlled application authorization generator derived from proposals, approval-ledger state, validation manifests, application gates, application packets, and dry-run plans
- added authorization-layer fields for authorization state, signoff requirements, authorization windows/expiry, final pre-execution conditions, and conservative execution authority defaults
- added runtime-generated controlled application authorization artifacts in JSON and Markdown without model mutation, auto-authorization, or pipeline/scheduler changes

## v2.7-controlled-application-execution-intents-slice-1
- added a read-only controlled application execution-intent generator derived from proposals, approval-ledger state, validation manifests, application gates, application packets, dry-run plans, and authorization records
- added execution-intent fields for intent status/readiness, required final checks, required operator role, execution blockers, rollback references, and linked source-path traceability
- added runtime-generated execution-intent artifacts in JSON and Markdown without model mutation, auto-execution, or pipeline/scheduler changes

## v1.6-operator-automation-slice-2
- added a separate local automation policy overlay with configurable escalation/reminder thresholds, severity weighting, routing rules, and handoff inclusion rules
- added a merged automation plan artifact that overlays local policy on the read-only automation queue without mutating workflow state
- preserved automation queue, worklist, dashboard, and pipeline outputs as read-only inputs with no scheduler or canonical schema changes

## v1.6-operator-automation-slice-1
- added a read-only automation and escalation queue derived from the operator worklist
- flagged escalation, reminder, priority-boost, and handoff recommendations without mutating workflow state automatically
- added runtime-generated JSON and Markdown automation queue artifacts without changing pipeline or scheduler behavior
