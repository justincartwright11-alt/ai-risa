# AI-RISA Standard Smoke Pack

This is the fixed set of known-good matchups for baseline regression:

- simon_yanez_amplified
- mckinney_nelson_amplified
- jenkins_braga_amplified
- matchup_fighter_israel_adesanya_vs_fighter_joe_pyfer

**Usage:**
- Rerun this pack only when upstream code changes.
- Use as baseline for regression and stability checks.
- Do not add/remove matchups unless a new real failure is discovered and validated.

---

## Validated Event Card: UFC 300 (2024-04-13)

All 13 UFC 300 matchups and fighter profiles were validated in the runtime root:

	C:\Users\jusin\ai_risa_data

Validated files are now tracked in the repo and match the runtime root state as of this commit.

Validation performed: deterministic, halt-on-failure, strict repo hygiene.

See commit: "Add UFC 300 event card and validated matchup data"
