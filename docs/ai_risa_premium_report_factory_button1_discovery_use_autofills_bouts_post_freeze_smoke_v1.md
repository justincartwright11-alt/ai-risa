# AI-RISA Premium Report Factory — Button 1 Discovery Use Autofills Bouts Post-Freeze Smoke v1

**Slice:** `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-post-freeze-smoke-v1`
**Implementation commit:** `e7edc98`
**Implementation tag:** `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-implementation-v1`
**Smoke date:** 2026-05-02
**Server:** `http://127.0.0.1:5000` (PID 43540, `python -m operator_dashboard.app`)
**Operator:** Operator

---

## Smoke Scope

Targeted live UI smoke for the locked behavior:

- Click **Use** on discovered event.
- Intake fields are pre-filled.
- Manual Input is pre-filled with bout lines.
- Parse Preview succeeds.
- Save succeeds with explicit operator approval.
- Button 2 sees the saved fight.
- No-bouts fallback message appears and Manual Input is cleared.

---

## Smoke 1 — Discovery Use autofills Ares FC 39 bout text

**UI flow:**

1. Open local dashboard at `http://127.0.0.1:5000`.
2. Click **Run Official-Source Discovery**.
3. In discovered rows, click **Use** for `Ares FC 39: Jbalia vs. Diatta`.

**Observed results:**

- `event_name` = `Ares FC 39: Jbalia vs. Diatta`
- `event_date` = `2026-04-03`
- `source_reference` = `events/ares_fc_39_2026_04_03.json`
- `raw_card_text` = `Aboubakar Jbalia vs Cherif Diatta`
- Status = `Ares FC 39: Jbalia vs. Diatta selected. 1 bouts loaded into Manual Input. Event and bout list loaded. Click Parse Preview.`

**Verdict: PASS**

- Use action pre-filled metadata and bout text from discovery row.
- Manual Input no longer remains empty for this discovered event.

---

## Smoke 2 — Parse Preview succeeds after Use autofill

**UI flow:**

1. With Ares row already loaded via **Use**, click **Parse Preview**.

**Observed results:**

- Status = `Preview loaded: 1 row(s) parsed.`
- Parsed counter = `| Parsed: 1 (1 ready, 0 needs_review)`
- Preview table row:
  - Fighter A: `Aboubakar Jbalia`
  - Fighter B: `Cherif Diatta`
  - Parse Status: `parsed`
  - Readiness Score: `80`

**Verdict: PASS**

- Parse path works directly from Use-populated Manual Input.

---

## Smoke 3 — Save and Button 2 queue visibility

**UI flow:**

1. Check approval: `I approve saving selected matchups to queue/database`.
2. Click **Save Selected**.
3. Click **Refresh Saved Fight Queue** in Button 2.

**Observed results:**

- Save status = `Save complete: 1 accepted, 0 rejected.`
- Saved table row:
  - Matchup ID: `prf_q_7b1e2a0d1275b54a`
  - Fighter A: `Aboubakar Jbalia`
  - Fighter B: `Cherif Diatta`
  - Queue Status: `saved`
- Button 2 status = `Queue loaded: 1 saved fight(s).`
- Button 2 queue row includes:
  - `Aboubakar Jbalia`
  - `Cherif Diatta`
  - Event `Ares FC 39: Jbalia vs. Diatta`

**Verdict: PASS**

- Approval-gated save works.
- Button 2 sees the saved fight from Button 1.

---

## Smoke 4 — No-bouts fallback on Use

**UI flow:**

1. In discovery rows, click **Use** for `Boxing: Wilder vs Chisora` (`0 bouts`).

**Observed results:**

- `event_name` updated to `Boxing: Wilder vs Chisora`
- `event_date` updated to `2026-04-04`
- `source_reference` updated to `events/boxing_o2_arena_2026_04_04.json`
- Manual Input textarea cleared (empty)
- Status includes exact fallback text:
  - `This discovered event has no bout list. Paste matchups manually.`

**Verdict: PASS**

- No-bouts branch behaves as designed: clear textarea and explicit operator guidance.

---

## Scope guard verification

Verified during smoke:

- No Button 2 behavior changes beyond expected queue visibility after save.
- No Button 3 interaction required for this slice.
- No endpoint additions introduced.
- `operator_dashboard/app.py` unchanged in implementation slice.

---

## Smoke Summary

| Scenario | Result |
|---|---|
| Use on Ares FC 39 pre-fills fields + Manual Input bout line | PASS |
| Parse Preview after Use returns parsed row | PASS |
| Save Selected with approval succeeds and Button 2 sees saved fight | PASS |
| Use on zero-bout event clears textarea and shows fallback message | PASS |

**Overall smoke verdict: PASS — implementation behavior matches locked target and fallback requirements.**
