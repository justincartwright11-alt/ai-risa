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
