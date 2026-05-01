# AI-RISA Premium Report Factory MVP — Phase 3 PDF Report Builder Design v1

## Builder Purpose

Convert operator-approved saved upcoming fight queue entries into customer-ready premium PDF reports. The builder operates entirely within the Phase 3 boundary: read from queue, generate reports, export to `ops/prf_reports/`, update `report_status`. No result lookup, no accuracy calibration, no learning, no billing, and no web discovery.

This document is a docs-only technical design. No implementation is authorized until this design is reviewed and a separate implementation slice is explicitly opened and test-gated.

---

## Baseline

| Field | Value |
|-------|-------|
| Parent checkpoint commit | `7cccee0` |
| Parent checkpoint tag | `ai-risa-premium-report-factory-mvp-phase3-pdf-report-standard-design-review-v1` |
| PDF Report Standard commit | `a800bba` |
| PDF Report Standard tag | `ai-risa-premium-report-factory-mvp-phase3-pdf-report-standard-design-v1` |
| Phase 2 archived baseline commit | `dfbacd4` |
| Phase 2 archived baseline tag | `ai-risa-premium-report-factory-mvp-phase2-approved-save-queue-archive-lock-v1` |
| Slice type | Docs-only technical design |

---

## Source Artifacts Reviewed

1. `docs/ai_risa_premium_report_factory_mvp_phase3_pdf_report_standard_design_v1.md` — governs report content, section contract, quality rules, export rules, and exclusions
2. `docs/ai_risa_premium_report_factory_mvp_phase3_pdf_report_standard_design_review_v1.md` — confirms standard is approved as governing content contract; carries two builder-design notes
3. `docs/ai_risa_premium_report_factory_mvp_phase2_approved_save_queue_archive_lock_v1.md` — defines the locked Phase 2 queue behavior; establishes the queue fields and endpoints the builder reads from

---

## Phase 3 Boundary

| In scope | Out of scope |
|----------|-------------|
| Read saved upcoming fight queue | Result lookup or accuracy comparison |
| Select one / many / all queue fights | Accuracy ledger updates |
| Generate premium PDF reports | Self-learning or model weight updates |
| Export to `ops/prf_reports/` | Web discovery or external data fetch |
| Update `report_status` to `generated` on success | Billing, payment, customer automation |
| Dashboard controls for selection and generation | Automatic distribution or emailing |
| Warnings/errors display | Fighter profile reports |
| | Global database expansion |
| | Mutation of fight records, predictions, or accuracy scores |

---

## Report Types

| Type | Description | Phase 3 |
|------|-------------|---------|
| Single matchup premium report | One queue fight — full 14-section analytical deep-dive | Yes |
| Full event-card report | All fights from one saved event in a single PDF package | Yes |
| Fighter profile report | Standalone fighter career/style profile | No — deferred |

---

## Required Report Section Contract

All reports must include the 14 sections defined in the locked PDF Report Standard, in fixed order. The builder must enforce this structurally — section presence must not be conditional on data availability. Sections with insufficient data render an explicit empty-state placeholder.

| # | Section | Empty-state behavior |
|---|---------|---------------------|
| 1 | Cover Page | Always populated from queue record — no empty-state needed |
| 2 | Headline Prediction | If model returns no prediction: "Prediction unavailable — insufficient data for this matchup." |
| 3 | Executive Summary | If unavailable: "Executive summary unavailable — insufficient matchup data." |
| 4 | Matchup Snapshot | Missing attributes rendered as "—"; comparison table rows marked "unavailable" |
| 5 | Decision Structure | If unavailable: "Decision structure analysis unavailable." |
| 6 | Energy Use and Gas Tank Projection | If unavailable: "Energy projection unavailable." |
| 7 | Fatigue Failure Points | If unavailable: "Fatigue analysis unavailable." |
| 8 | Mental Condition | If unavailable: "Mental condition profile unavailable." |
| 9 | Collapse Triggers | If unavailable: "Collapse trigger analysis unavailable." |
| 10 | Deception and Unpredictability | If unavailable: "Deception profile unavailable." |
| 11 | Round-by-Round Control Shifts | If unavailable: "Round-by-round projection unavailable." |
| 12 | Scenario Tree / Method Pathways | If unavailable: "Scenario pathways unavailable." |
| 13 | Risk Warnings | Always rendered — minimum: "Standard prediction caveats apply. See operator notes." |
| 14 | Operator Notes | If `notes` field empty: "No operator notes recorded." |

---

## Proposed Backend Touchpoints

### New files (implementation slice only — do not create in this design slice)

| File | Purpose |
|------|---------|
| `operator_dashboard/prf_report_builder.py` | Core PDF assembly — accepts a queue record and report type, returns a structured report object |
| `operator_dashboard/prf_report_content.py` | Content assembler — maps queue fields to 14 report sections, applies empty-state rules, enforces quality rules |
| `operator_dashboard/prf_report_export.py` | Export helper — renders structured report to PDF file, writes to `ops/prf_reports/`, returns file path and status |

### Existing file to extend (implementation slice only)

| File | Change |
|------|--------|
| `operator_dashboard/prf_queue_utils.py` | Add `update_report_status(queue_path, matchup_id, new_status)` helper — updates only `report_status` field on a saved queue record |

### Existing file to extend (implementation slice only)

| File | Change |
|------|--------|
| `operator_dashboard/app.py` | Add two new endpoints: `POST /api/premium-report-factory/reports/generate` and `GET /api/premium-report-factory/reports/list` |

---

## Proposed Dashboard Touchpoints

All controls are additions to the existing `#operator-prf-upcoming-queue-window` section. No existing Phase 2 controls are modified.

| Element | ID | Purpose |
|---------|----|---------|
| Per-row generate checkbox | `.operator-prf-report-matchup-checkbox` | Select individual queue rows for generation |
| Select All for generation | `#operator-prf-report-select-all` | Toggle all checkboxes |
| Generate Premium PDF Reports button | `#operator-prf-generate-reports-btn` | Trigger generation for selected rows |
| Operator approval checkbox | `#operator-prf-generate-approval` | Must be checked before generation |
| Report type selector | `#operator-prf-report-type-select` | `single_matchup` or `event_card` |
| Export results window | `#operator-prf-export-results-window` | Shows generation result table |
| Generated file path display | Within export results table | File name and path per report |
| Report status display | Within export results table | `generated`, `failed`, `partial` per row |
| Warnings/errors display | `#operator-prf-generate-warnings` | Non-blocking warnings from generation |

---

## Proposed Endpoints

### POST /api/premium-report-factory/reports/generate

Generate premium PDF reports for selected saved queue fights.

**Request contract:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `selected_matchup_ids` | array of strings | Yes | `matchup_id` values from saved queue |
| `report_type` | string | Yes | `single_matchup` or `event_card` |
| `operator_approval` | boolean | Yes | Must be `true` — rejected otherwise |
| `export_format` | string | No | `pdf` only for Phase 3 (default: `pdf`) |
| `notes` | string | No | Operator notes appended to each report |

**Response contract:**

| Field | Type | Description |
|-------|------|-------------|
| `ok` | boolean | True if at least one report generated successfully |
| `generated_at` | ISO 8601 string | Generation timestamp |
| `accepted_count` | integer | Reports successfully generated |
| `rejected_count` | integer | Requests rejected before generation |
| `generated_reports` | array | See generated_report fields below |
| `rejected_reports` | array | `{ matchup_id, reason }` per rejected request |
| `export_summary` | object | `{ output_folder, total_files, total_size_bytes }` |
| `warnings` | array | Non-fatal warnings (e.g. missing promotion field) |
| `errors` | array | Fatal errors (e.g. queue read failure) |

### GET /api/premium-report-factory/reports/list

List all generated reports in `ops/prf_reports/` with their metadata.

**Response contract:**

| Field | Type | Description |
|-------|------|-------------|
| `ok` | boolean | True if list was read successfully |
| `generated_at` | ISO 8601 string | Response timestamp |
| `reports` | array | See generated_report fields below |
| `total_count` | integer | Total report files found |
| `warnings` | array | Non-fatal warnings |
| `errors` | array | Fatal errors |

---

## Proposed `generated_report` Fields

| Field | Type | Description |
|-------|------|-------------|
| `report_id` | string | Deterministic SHA-256 ID: `prf_r_{hash[:16]}` |
| `matchup_id` | string | Source queue record matchup ID |
| `event_id` | string | Source queue record event ID |
| `fighter_a` | string | Fighter A name |
| `fighter_b` | string | Fighter B name |
| `event_name` | string | Event name |
| `event_date` | string | Event date (YYYY-MM-DD) |
| `promotion` | string | Promotion name |
| `report_type` | string | `single_matchup` or `event_card` |
| `report_status` | string | `generated`, `failed`, or `partial` |
| `export_format` | string | `pdf` |
| `file_name` | string | `ai_risa_premium_report_{event_id}_{matchup_id}_{YYYYMMDD}.pdf` |
| `file_path` | string | Full path within `ops/prf_reports/` |
| `generated_at` | ISO 8601 string | Export completion timestamp |
| `section_status` | object | `{ section_name: "complete" | "partial" | "unavailable" | "blocked" }` per section |
| `source_reference` | string | Source reference from queue record |
| `operator_notes` | string | Operator notes used in this report |

---

## Proposed Export Rules

| Rule | Detail |
|------|--------|
| Output folder | `ops/prf_reports/` — runtime-only, not committed |
| Filename | `ai_risa_premium_report_{event_id}_{matchup_id}_{YYYYMMDD}.pdf` — deterministic |
| Format | PDF only for Phase 3 |
| `report_status` update | Set to `generated` only after PDF write is confirmed complete |
| Failed export | `report_status` set to `failed` — must not be set to `generated` |
| Partial export | If PDF written but one or more sections are `blocked`: `report_status` set to `partial` |
| No auto-send | No email, webhook, or distribution trigger |
| No billing | No payment or customer notification |
| No external upload | No S3, CDN, or remote storage |
| Operator-initiated only | Export is always triggered by explicit operator action |

---

## Proposed Content Assembly Model

The content assembler (`prf_report_content.py`) maps available queue fields to report sections using the following priority order:

1. **Queue record fields** — `fighter_a`, `fighter_b`, `event_name`, `event_date`, `promotion`, `location`, `weight_class`, `ruleset`, `source_reference`, `notes`, `report_readiness_score`
2. **Existing prediction/report surfaces** — only if already computed and available in the system; no new model calls, no web fetch
3. **Empty-state placeholders** — for any section where data is not available

**Quality enforcement:**
- No raw JSON, no internal field names, no `matchup_id` or `temporary_matchup_id` in the report body
- Confidence expressed as plain-English band alongside any numeric value
- Limitations statement always present in Section 13 (Risk Warnings)
- AI-RISA branding, version, and generation timestamp on every page

---

## Section Status Model

| Status | Meaning |
|--------|---------|
| `complete` | Section rendered with full available data |
| `partial` | Section rendered with some data missing; placeholder used for missing parts |
| `unavailable` | Section rendered with full empty-state placeholder — no relevant data found |
| `blocked` | Section could not be rendered due to a processing error; report_status becomes `partial` |

---

## Report Readiness and Rejection Behavior

| Condition | Action |
|-----------|--------|
| Missing `fighter_a` or `fighter_b` | Reject — cannot generate without fighter names |
| Queue row has `queue_status = needs_review` | Reject — only `saved` rows are eligible |
| Unsupported `report_type` | Reject — only `single_matchup` and `event_card` accepted |
| `operator_approval` not `true` | Reject — generation requires explicit approval |
| Missing `promotion` | Warn — proceed with empty-state for promotion fields |
| Missing `source_reference` | Warn — proceed with empty-state for source fields |
| Missing `event_date` | Warn — proceed with empty-state for date fields |
| PDF write fails mid-render | Set `report_status` to `failed` — do not set `generated` |

**No silent partial export.** All rejection reasons must be returned in the `rejected_reports` array.

---

## Safety and Governance Guardrails

| Guardrail | Enforcement |
|-----------|-------------|
| No result lookup | `prf_report_builder.py` and `prf_report_content.py` must not call any result-lookup or web-fetch function |
| No accuracy comparison | No accuracy ledger read or write during generation |
| No learning or calibration update | No scoring weight, model parameter, or ledger update during generation |
| No web discovery | No external HTTP call during generation |
| No customer billing | No payment processing or notification |
| No automatic distribution | No email, webhook, or remote upload |
| No token semantic changes | Phase 2 queue tokens unchanged |
| No scoring rewrite | `report_readiness_score` is read-only during generation |
| No global ledger write | `prf_report_export.py` writes only to `ops/prf_reports/` and updates `report_status` in the queue file |

---

## Future Implementation Test Plan

The following tests must be written and passing before any implementation commit is made:

| # | Test | Scope |
|---|------|-------|
| 1 | Generate endpoint rejects missing `operator_approval` | Backend |
| 2 | Generate endpoint rejects `needs_review` queue rows | Backend |
| 3 | Generate endpoint rejects missing fighter names | Backend |
| 4 | Generate endpoint rejects unsupported `report_type` | Backend |
| 5 | Successful generation returns `accepted_count >= 1` | Backend |
| 6 | Generated PDF file exists at expected path with deterministic filename | Backend |
| 7 | `report_status` is `generated` only after confirmed file write | Backend |
| 8 | Failed export sets `report_status` to `failed`, not `generated` | Backend |
| 9 | All 14 required sections present in `section_status` | Backend |
| 10 | Missing analysis data uses defined empty-state placeholder, not blank | Backend |
| 11 | No result/accuracy/learning/billing/web call occurs during generation | Backend |
| 12 | Queue list endpoint still returns correct saved rows after generation | Backend (regression) |
| 13 | Phase 2 save endpoint unaffected by Phase 3 additions | Backend (regression) |
| 14 | All pre-existing tests remain green | Backend (regression) |
| 15 | Dashboard generation controls are present and operator-approval-gated | Frontend (token check) |

---

## Explicit Non-Goals

- No result lookup of any kind during or after PDF generation
- No accuracy ledger read or write triggered by PDF generation
- No model self-learning, weight update, or calibration triggered by PDF generation
- No web discovery, external HTTP call, or scraping during generation
- No billing, payment processing, or customer notification
- No automatic distribution, emailing, or remote upload of generated PDFs
- No fighter profile report type in Phase 3
- No expansion of the global fight database beyond saved queue records
- No mutation of existing fight records, prediction records, or accuracy scores
- No change to Phase 2 queue endpoints or queue helper behavior
- No change to Phase 1 report or prediction endpoints

---

## Implementation Readiness Verdict

The Phase 3 PDF Report Builder design is **approved only as a docs-only technical design boundary.**

- The content contract (14 sections, quality rules, export rules, exclusions) is fully specified by the locked PDF Report Standard
- The API contract (request/response fields, rejection rules, section status model) is fully defined above
- The backend and dashboard touchpoints are named and scoped
- The test plan is specified
- No implementation code is present

**Actual implementation remains blocked** until:

1. This builder design is reviewed and locked under slice `ai-risa-premium-report-factory-mvp-phase3-pdf-report-builder-design-review-v1`
2. A separate implementation slice is explicitly opened: `ai-risa-premium-report-factory-mvp-phase3-pdf-report-builder-implementation-v1`
3. All tests in the test plan above are written and passing before the implementation commit is made
