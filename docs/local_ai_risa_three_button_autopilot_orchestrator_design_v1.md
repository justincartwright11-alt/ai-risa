# Local AI-RISA Three-Button Autopilot Orchestrator — Design v1

**Slice:** `local-ai-risa-three-button-autopilot-orchestrator-design-v1`
**Status:** DESIGN LOCKED — DOCS ONLY
**Date:** 2026-05-15

---

## 1. Purpose

The operator dashboard surface is intentionally simple: three buttons, three approval gates.
Underneath those three buttons sits a **local AI orchestration layer** that does the heavy work:
searching, extracting, normalizing, ranking, generating, QA-checking, comparing, and recommending.

The AI does all the labor. The operator controls permission.

This document defines:
- What the local AI orchestrator does behind each button
- How jobs are modeled, tracked, and surfaced
- How approval gates are enforced before any permanent action
- Where advanced diagnostics live (Advanced Dashboard only)
- What is explicitly out of scope for this layer

---

## 2. Product Rule

> **AI-RISA local AI controls the workflow. The operator controls permission.**

The local AI orchestrator may:
- Search, fetch, parse, extract, normalize, rank, score, classify, generate, preview, compare, and recommend
- Surface results as **read-only previews** at any stage
- Queue actions for operator review

The local AI orchestrator may **not** — without an explicit operator approval token:
- Write to the fight queue or global database
- Export or deliver a customer PDF
- Apply a result to the accuracy ledger
- Update any learning or calibration parameter
- Modify a prediction or report

---

## 3. Visible Operator Surface

The normal dashboard remains exactly:

```
┌─────────────────────────────────────────────────────────┐
│  AI-RISA Premium Report Factory — Operator Dashboard    │
├──────────────────┬──────────────────┬───────────────────┤
│  [Button 1]      │  [Button 2]      │  [Button 3]       │
│  Find Fights     │  Generate PDFs   │  Find Results     │
│  🔒 Gate 1       │  🔒 Gate 2       │  🔒 Gate 3        │
└──────────────────┴──────────────────┴───────────────────┘
           Normal mode: nothing else visible
```

**No new buttons.** No diagnostics panels. No job queues. No telemetry widgets.
Every additional control lives at `/advanced-dashboard`.

---

## 4. Hidden Local AI Layer

The orchestrator runs **behind** the three buttons. The operator sees only summaries and gates.

```
Operator click
     │
     ▼
┌────────────────────────────────────────┐
│        Local AI Orchestrator           │
│  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ Job Queue│  │ Job Types│  │Safety│ │
│  │  (async) │  │ (typed)  │  │ Flags│ │
│  └────┬─────┘  └────┬─────┘  └──┬───┘ │
│       └─────────────┴──────────┘      │
│            Preview Response           │
└────────────────────────────────────────┘
     │
     ▼
Operator sees: simple summary + gate prompt
     │
     ▼ (operator approves)
Approval Token issued → permanent action unlocked
```

The local AI layer is stateless from the operator's perspective between clicks.
Jobs can be re-run without side effects until an approval token is issued.

---

## 5. Button 1 Orchestration — Find Fights

**Operator action:** Click "Find Fights"

**Local AI steps (in order, all preview-only until gate):**

| Step | Job Type | Input | Output |
|------|----------|-------|--------|
| 1 | `discovery_job` | Promotion URLs / date range | Raw event page HTML / JSON |
| 2 | `extraction_job` | Raw event pages | Fighter A vs Fighter B pairs |
| 3 | `normalization_job` | Raw fighter names | Normalized names (accents stripped, canonical format) |
| 4 | `dedup_job` | Normalized fight list | Deduplicated fight list (flag repeats from existing queue) |
| 5 | `ranking_job` | Deduplicated fights | Ranked list: report value, data readiness, source confidence |
| 6 | `queue_candidate_job` | Ranked fights | Save candidates: preview only, no write yet |

**Gate 1 triggers here:** Operator reviews ranked save candidates → approves → queue write.

**What the operator sees (normal mode):**
- Count of fights found
- Count ranked as ready
- Count of duplicates detected
- "Approve to save to queue" gate prompt

**What is blocked until Gate 1:**
- No fight written to global database
- No queue entry created
- No fight committed for report generation

---

## 6. Button 2 Orchestration — Generate PDFs

**Operator action:** Click "Generate Report" (after queue has approved fights)

**Local AI steps (in order, all preview-only until gate):**

| Step | Job Type | Input | Output |
|------|----------|-------|--------|
| 1 | `report_generation_job` | Approved queue fight | Full report content (all 26 sections, v29 composition) |
| 2 | `report_quality_job` | Generated report | QA pass/fail: placeholder check, word count, section coverage |
| 3 | `pdf_preview_job` | QA-passed report | PDF preview (local temp file, not exported) |
| 4 | `delivery_candidate_job` | PDF preview | Delivery candidate: path, QA result, fight ref, timestamp |

**Gate 2 triggers here:** Operator reviews QA summary + PDF preview → approves → export/delivery.

**What the operator sees (normal mode):**
- Fight name and report status
- QA summary (pass/fail, blocking issues if any)
- "Approve for customer delivery" gate prompt

**What is blocked until Gate 2:**
- No PDF written to customer-facing location
- No email / delivery triggered
- No export path exposed outside operator review

---

## 7. Button 3 Orchestration — Find Results

**Operator action:** Click "Find Results"

**Local AI steps (in order, all preview-only until gate):**

| Step | Job Type | Input | Output |
|------|----------|-------|--------|
| 1 | `result_search_job` | Waiting rows (fights in queue with no result yet) | Candidate result sources per row |
| 2 | `result_match_job` | Candidates + waiting rows | Row-level state: Results Found / Needs Source / Conflict / No Result Yet / Ready to Compare |
| 3 | `accuracy_comparison_job` | Matched results + saved predictions | Prediction vs actual per fight: winner, method, round |
| 4 | `calibration_recommendation_job` | Accuracy comparison results | Recommended calibration delta, confidence, risk flag |

**Gate 3 triggers here:** Operator reviews accuracy summary + calibration recommendations → approves → durable result apply / learning update.

**What the operator sees (normal mode):**
- Count per state (Results Found, Needs Source, Conflict, No Result Yet, Ready to Compare)
- "Preview complete — confirm to apply results" gate prompt (no auto-apply)

**What is blocked until Gate 3:**
- No result written to accuracy ledger
- No prediction mutated
- No learning parameter updated
- No calibration write performed
- No auto-apply

---

## 8. Approval Gate Model

Three gates, one per button. Each gate follows a common contract.

### Gate Contract

```
Gate {
  gate_id:              string        // "gate_1" | "gate_2" | "gate_3"
  label:                string        // human-readable name
  button:               1 | 2 | 3
  preview_summary:      dict          // what the AI found / what will change
  source_provenance:    list[str]     // URLs, job_ids, timestamps
  risk_display:         list[str]     // blocking reasons, anomalies, warnings
  operator_token:       string|null   // null = not yet approved
  audit_entry:          dict          // timestamp, operator_id, approved/denied
  rollback_pointer:     string|null   // snapshot key for reversible actions
  mutation_scope:       list[str]     // explicit list of what will be written on approval
}
```

### Gate Definitions

#### Gate 1 — Approve Save Fights

| Field | Value |
|-------|-------|
| `gate_id` | `gate_1` |
| `label` | Approve Save Fights to Queue |
| `preview_summary` | fights found, ranked list, duplicate flags |
| `source_provenance` | promotion URLs, discovery job IDs |
| `risk_display` | duplicate warnings, low-confidence sources |
| `mutation_scope` | `["fight_queue.json", "global_database.fights"]` |
| `rollback_pointer` | queue snapshot before write |

#### Gate 2 — Approve Customer PDF Delivery

| Field | Value |
|-------|-------|
| `gate_id` | `gate_2` |
| `label` | Approve Customer PDF Delivery |
| `preview_summary` | fight name, QA result, section coverage |
| `source_provenance` | report generation job ID, QA job ID |
| `risk_display` | QA failures, placeholder text detected, short sections |
| `mutation_scope` | `["pdf_exports/", "delivery_log.json"]` |
| `rollback_pointer` | N/A (export is write-once; rollback = delete export) |

#### Gate 3 — Approve Result Apply / Learning Review

| Field | Value |
|-------|-------|
| `gate_id` | `gate_3` |
| `label` | Approve Result Apply and Learning Review |
| `preview_summary` | result states, accuracy delta, calibration recommendations |
| `source_provenance` | result source URLs, match job IDs |
| `risk_display` | conflicts, low-confidence matches, large calibration deltas |
| `mutation_scope` | `["ops/accuracy/accuracy_ledger.json", "calibration_state.json"]` |
| `rollback_pointer` | ledger snapshot before apply |

---

## 9. Local AI Job Model

All orchestrator work is expressed as typed jobs. Jobs are the unit of tracking, preview, and audit.

### Base Job Schema

```python
{
  "job_id":             str,    # UUID, auto-generated
  "job_type":           str,    # one of the defined types below
  "source_button":      int,    # 1 | 2 | 3
  "input_ref":          dict,   # {type, key, snapshot_hash}
  "output_preview":     dict,   # read-only preview of what was produced
  "status":             str,    # "pending" | "running" | "complete" | "failed" | "blocked"
  "blocking_reasons":   list,   # list of human-readable block strings
  "provenance":         dict,   # {source_urls, timestamps, engine_version}
  "mutation_performed": False,  # always False until gate approval
  "approval_required":  bool,   # True for any job that precedes a permanent action
  "created_at":         str,    # ISO timestamp
  "completed_at":       str|None,
}
```

### Job Type Registry

| Job Type | Button | Reads | Writes (after gate) |
|----------|--------|-------|---------------------|
| `discovery_job` | 1 | Web (official sources) | None |
| `extraction_job` | 1 | Raw HTML / JSON | None |
| `normalization_job` | 1 | Raw names | None |
| `dedup_job` | 1 | Current queue | None |
| `ranking_job` | 1 | Fight list | None |
| `queue_candidate_job` | 1 | Ranked list | None (preview only) |
| `report_generation_job` | 2 | Approved fight data | None |
| `report_quality_job` | 2 | Generated report | None |
| `pdf_preview_job` | 2 | QA-passed report | Local temp only |
| `delivery_candidate_job` | 2 | PDF preview | None (preview only) |
| `result_search_job` | 3 | Trusted sources (read-only) | None |
| `result_match_job` | 3 | Candidates + rows | None |
| `accuracy_comparison_job` | 3 | Matched results + predictions | None |
| `calibration_recommendation_job` | 3 | Accuracy comparison | None |

**After gate approval only:**

| Approved Action | Triggered By | Writes |
|-----------------|-------------|--------|
| `queue_write` | Gate 1 | fight queue, database |
| `pdf_export` | Gate 2 | pdf_exports/, delivery_log |
| `result_apply` | Gate 3 | accuracy_ledger.json |
| `calibration_write` | Gate 3 (explicit) | calibration_state.json |

---

## 10. Safety Telemetry Contract

Every local AI response — at every layer (job output, gate summary, API response) — must include:

```python
{
  "preview_only":             bool,   # True for all responses before gate approval
  "mutation_performed":       bool,   # False until gate approval token issued
  "queue_write_performed":    bool,   # False until Gate 1 approved
  "report_export_approved":   bool,   # False until Gate 2 approved
  "durable_write_performed":  bool,   # False until gate approval token issued
  "learning_apply_performed": bool,   # False until Gate 3 approved
  "calibration_write_performed": bool, # False until Gate 3 approved
  "auto_apply_performed":     bool,   # Always False — no auto-apply ever
  "operator_approval_required": bool, # True for any action that would persist
}
```

This contract is **immutable**. Any response that sets `mutation_performed=True` without
a verified approval token is a governance violation and must be caught in tests.

---

## 11. Advanced Dashboard Placement

The Advanced Dashboard (`/advanced-dashboard`) is the **only** location where operators or
developers can view internal orchestrator state.

### Advanced Dashboard surfaces (future implementation):

| Panel | Contents |
|-------|----------|
| Job Queue | All jobs, status, timing, input/output refs |
| Source Traces | Per-job URL fetches, response codes, snippet previews |
| Engine Outputs | Raw classifier scores, ranking signals, match scores |
| Failed Jobs | Error details, retry controls, manual override prompts |
| Calibration Preview | Recommended deltas, confidence intervals, risk flags |
| Audit Trail | Full approval history: who, when, what was written |
| Rollback Records | Snapshots before each Gate approval, restore controls |

### Normal dashboard must NEVER show:
- Job IDs or job status widgets
- Source URLs or trace output
- Calibration deltas or model internals
- Audit trail entries
- Rollback controls
- Error stack traces
- `row_details`, `telemetry` raw fields

---

## 12. Non-Goals

This design explicitly excludes:

1. **Automatic customer delivery** — PDFs are never sent without Gate 2 approval.
2. **Automatic learning** — Calibration is never updated without Gate 3 approval.
3. **Automatic queue writes** — Fights are never saved without Gate 1 approval.
4. **Parallel / background orchestration** without operator-visible status — all jobs must be inspectable.
5. **External API calls without provenance** — every web fetch must be logged with URL + timestamp.
6. **Multi-agent delegation** — the orchestrator is a single local runner, not a distributed agent network.
7. **Customer-facing AI responses** — the AI only assists the operator, not the end customer directly.
8. **Prediction mutation** — predictions are read-only inputs to comparison; they are never rewritten by the orchestrator.
9. **Report content mutation without gate** — generated report content is preview only until Gate 2.
10. **Auto-rollback** — rollbacks require explicit operator action, not automatic recovery.

---

## 13. Future Implementation Slices

Implementation should proceed in this order after design lock:

| Slice | Scope | Gate Touched |
|-------|-------|--------------|
| `local-ai-orchestrator-job-schema-v1` | Define Python job dataclasses + schema validation | None |
| `local-ai-orchestrator-job-runner-v1` | Base job runner: execute, status, telemetry | None |
| `button1-discovery-job-wire-v1` | Wire discovery_job to Button 1 | Pre-Gate 1 |
| `button1-extraction-ranking-wire-v1` | Wire extraction + ranking jobs to Button 1 | Pre-Gate 1 |
| `button1-gate1-save-wire-v1` | Wire Gate 1 approval to queue write | Gate 1 |
| `button2-report-generation-job-wire-v1` | Wire report_generation_job + QA to Button 2 | Pre-Gate 2 |
| `button2-gate2-pdf-export-wire-v1` | Wire Gate 2 approval to PDF export | Gate 2 |
| `button3-result-search-job-wire-v1` | Wire result_search_job to Button 3 (replaces direct executor call) | Pre-Gate 3 |
| `button3-accuracy-comparison-job-wire-v1` | Wire accuracy_comparison_job to Button 3 | Pre-Gate 3 |
| `button3-gate3-result-apply-wire-v1` | Wire Gate 3 approval to result apply + calibration write | Gate 3 |
| `advanced-dashboard-job-queue-panel-v1` | Add job queue / audit trail panels to Advanced Dashboard | None |

Each slice must:
- Pass the full prior regression suite before merging
- Add its own test file
- Not modify the normal dashboard surface
- Not weaken any approval gate

---

## 14. Final Verdict

This design is **approved for implementation**.

The three-button surface is preserved. All complexity is hidden. Gates are hardened.
The local AI layer is fully specced: job types, gate contracts, telemetry, placement rules.

The next safe implementation slice is:
**`local-ai-orchestrator-job-schema-v1`** — define Python job dataclasses and schema validation,
with no behavior change to the existing dashboard or any existing routes.

```
Core product rule confirmed:
  AI-RISA local AI controls the workflow.
  The operator controls permission.
```
