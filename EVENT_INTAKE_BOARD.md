# Event Ingestion Operational Intake Board

| Event                        | Promotion | Date       | Source URL | Status    | Runtime Root                | Repo Root                   | First Bout Validated | Full Card Validated | Data Commit | Smoke Pack Updated | Notes / Risks |
|------------------------------|-----------|------------|------------|-----------|-----------------------------|-----------------------------|----------------------|---------------------|-------------|--------------------|---------------|
| UFC 328: Makhachev vs. Tsarukyan | UFC       | 2024-06-01 | [TBD]      | queued (provisional)    | TBD                         | TBD                         |                      |                     |             |                    |               |
| Stevenson vs. Navarrete      | Top Rank  | 2024-07-06 | [TBD]      | queued (provisional)    | TBD                         | TBD                         |                      |                     |             |                    |               |
| Superlek vs. Rodtang II      | ONE       | 2024-05-10 | [TBD]      | queued (provisional)    | TBD                         | TBD                         |                      |                     |             |                    |               |
| UFC 300                      | UFC       | 2024-04-13 | [TBD]      | committed | C:\Users\jusin\ai_risa_data | C:\ai_risa_data            | Yes                  | Yes                | Yes        | Yes               |               |
| UFC 327                      | UFC       | 2026-04-12 | [TBD]      | committed | C:\Users\jusin\ai_risa_data | C:\ai_risa_data            | Yes                  | Yes                | Yes        | Yes               |               |
| GLORY 107                    | GLORY     | 2026-04-26 | [TBD]      | committed | C:\Users\jusin\ai_risa_data | C:\ai_risa_data            | Yes                  | Yes                | Yes        | Yes               |               |

---

## Standard Event Ingestion Workflow

1. Planning pass
2. Reconcile naming/date conflicts
3. Create one validated first bout only
4. Stop on first real failure
5. Expand to full card only after first bout passes
6. Commit data slice
7. Update smoke pack
8. Return to hold

---

## Runtime Root Discipline
- Every event slice must declare:
  - Active runtime root
  - Repo root
  - Copy direction between repo data and runtime data
- No mixing roots without explicit reconciliation.

---

## Hard Rules
- No speculative code edits
- No boundary-file edits unless evidence forces them
- One event at a time
- Validate one bout at a time until the first path is proven
- Stop on first real failure and classify the layer
