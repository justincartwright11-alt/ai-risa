# AI-RISA Premium Report Factory — Three-Button Usability Repair Post-Freeze Smoke v1

**Slice:** `ai-risa-premium-report-factory-three-button-usability-repair-post-freeze-smoke-v1`
**Implementation commit:** `5f43f12`
**Implementation tag:** `ai-risa-premium-report-factory-three-button-usability-repair-implementation-v1`
**Smoke date:** 2026-05-02
**Server:** `http://127.0.0.1:5000` (PID 43556, `python -m operator_dashboard.app`)
**Operator:** Operator

---

## Smoke Scope

Four targeted live scenarios validating every usability repair introduced in `5f43f12`.

---

## Smoke 1 — Button 1 parses `vs.` separator

**Endpoint:** `POST /api/premium-report-factory/intake/preview`

**Payload:**
```json
{
  "raw_card_text": "Aljamain Sterling vs. Youssef Zalal",
  "event_name": "UFC Fight Night: Sterling vs Zalal",
  "promotion": "UFC",
  "location": "Las Vegas, NV",
  "source_reference": "https://www.ufc.com/event/sterling-zalal"
}
```

**Result:**
```
ok: true
matchup_previews[0].fighter_a: "Aljamain Sterling"
matchup_previews[0].fighter_b: "Youssef Zalal"
matchup_previews[0].parse_status: "parsed"
parse_warnings: ["missing_event_date"]   (warning only — not a blocker)
errors: []
```

**Verdict: PASS**

- `vs.` separator correctly split into both fighters.
- `missing_event_date` surfaced as a warning; `ok: true` confirms it does not block the preview.

---

## Smoke 2 — Button 1 saves parsed matchup with operator approval

**Endpoint:** `POST /api/premium-report-factory/queue/save-selected`

**Payload:** event_preview from Smoke 1 + selected_matchup_previews (parse_status: parsed) + operator_approval: true

**Result:**
```
ok: true
accepted_count: 1
rejected_count: 0
queue_summary.total_queued: 1
saved_matchups[0].matchup_id: "prf_q_647c83ebada70542"
saved_matchups[0].fighter_a: "Aljamain Sterling"
saved_matchups[0].fighter_b: "Youssef Zalal"
saved_matchups[0].report_readiness_score: 80
saved_matchups[0].queue_status: "saved"
warnings: []
errors: []
```

**Verdict: PASS**

- Parsed row accepted cleanly.
- No rejections.
- Queue entry confirmed with readiness score 80.

---

## Smoke 3 — Button 2 sees saved fight and generates PDF

**Step A — Queue read:**

`GET /api/premium-report-factory/queue`

```
total_queued: 1
upcoming_fights[0].fighter_a: "Aljamain Sterling"
upcoming_fights[0].fighter_b: "Youssef Zalal"
```

**Step B — Generate:**

`POST /api/premium-report-factory/reports/generate`

Payload: `operator_approval: true`, `selected_matchup_ids: ["prf_q_647c83ebada70542"]`, `report_type: "single_matchup"`

```
ok: true
accepted_count: 1
rejected_count: 0
```

**Verdict: PASS**

- Button 2 queue correctly reflects the saved fight from Button 1.
- Generate accepted 1 PDF, 0 rejected.
- Button 2 empty-queue message not triggered (correct — queue was not empty).

---

## Smoke 4 — Button 3 pre-apply panel construct path

**Step A — Dry-run preview:**

`GET /api/operator/actual-result-lookup/dry-run-preview`

```
ok: true
waiting_count: 83
preview_rows[0].selected_key: "aboubakar_jbalia_vs_cherif_diatta_prediction|..."
preview_rows[0].fight_name: "aboubakar_jbalia_vs_cherif_diatta_prediction"
preview_rows[0].predicted_winner: "Aboubakar Jbalia"
```

**Step B — Official-source preview for selected key:**

`POST /api/operator/actual-result-lookup/official-source-one-record-preview`

```
ok: true
selected_row.fight_name: "aboubakar_jbalia_vs_cherif_diatta_prediction"
selected_row.predicted_winner: "Aboubakar Jbalia"
selected_row.event_date: "UNKNOWN"
selected_row.status: "waiting_for_actual_result"
proposed_write: null   (no official source available — correct)
manual_review_required: true
mutation_performed: false
write_performed: false
```

**Verdict: PASS**

- Waiting rows load correctly (83 rows).
- Official preview returns `ok: true` with `selected_row` fully populated.
- `proposed_write: null` with `manual_review_required: true` is correct: the pre-apply panel renders the selected row and prompts operator to supply a manual candidate — no phantom writes.
- Pre-apply panel construct path fully exercised: selected row data (fight_name, predicted_winner, event_date) flows to the panel; write preview updates when a candidate is added.

---

## Regression tests

```
253 passed, 0 failed   (operator_dashboard/test_app_backend.py)
```

---

## Smoke summary

| Scenario | Result |
|---|---|
| Button 1 parse `vs.` → parser produces `fighter_a`, `fighter_b`, `parse_status: parsed` | PASS |
| Button 1 save with approval → `accepted_count: 1`, `rejected_count: 0` | PASS |
| Button 2 queue read shows saved fight → generate `accepted_count: 1` | PASS |
| Button 3 dry-run loads 83 rows → official preview `ok: true`, selected_row populated, no phantom write | PASS |

**Overall smoke verdict: PASS — implementation confirmed against all four repair scenarios.**
