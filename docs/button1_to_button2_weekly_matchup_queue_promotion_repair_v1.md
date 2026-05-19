# Button 1 to Button 2 Weekly Matchup Queue Promotion Repair v1

## Overview
This document records the repair and live proof for the canonical promotion of approved, ready matchups from Button 1 (Find & Build Fight Queue) to Button 2 (Generate Premium PDF Reports) in the AI-RISA Premium Report Factory dashboard.

**Slice:** `button1-to-button2-weekly-matchup-queue-promotion-repair-v1`

---

## Tasks Completed
- Task 1–2: Root cause, counts, missing matchups, patch targets identified — **DONE**
- Task 3: Canonical promotion endpoint implemented and smoke verified — **DONE**
- Task 4: UI controls and endpoint wiring implemented — **DONE**
- Task 5: Queue-loader canonical verification — **DONE**
- Task 6: New regression suite, all required tests passing — **DONE**
- Task 7: Live runtime proof (promotion, queue refresh, PDF generation, text extraction) — **DONE**

---

## Live Proof Summary (May 19, 2026)

- **Port:** 5050

### Button 1 Promotion
- promoted_count=0
- duplicate_count=15
- skipped_count=0
- queue_before_count=21
- queue_after_count=21

### Button 2 Refresh Queue
- total_rows=21
- ready_count=21

### PDF Generation
- **Single:** Alex Pereira vs Jiri Prochazka — UFC 300 (generated=1)
- **Multi:** Islam Makhachev vs Dustin Poirier — UFC 300; Max Holloway vs Justin Gaethje — UFC 300 (generated=2)

### PDF Text Extraction Proof
- Islam Makhachev: true
- Dustin Poirier: true
- UFC 300: true

---

## Governance Flags

- **Promotion duplicate-only run:**
  - queue_write_performed: false
- **Batch generation:**
  - report_generation_performed: true
  - queue_write_performed: false
  - delivery_performed: false
  - external_api_delivery_performed: false
  - learning_apply_performed: false
  - calibration_write_performed: false
  - button3_mutation_performed: false

---

## Environment & Warnings
- **WeasyPrint import warning**: Present (OSError), but non-blocking — PDF generation succeeded through current runtime path.
- **No delivery, learning, or mutation side effects**: All governance flags confirmed as false except report_generation_performed.

---

## Next Steps
- Create JSON summary
- Final validation (pytest)
- Commit and tag

---

## File Locations
- Canonical promotion endpoint: `operator_dashboard/app.py`
- UI controls: `operator_dashboard/templates/index.html`
- Tests: `operator_dashboard/test_button1_to_button2_weekly_matchup_queue_promotion_repair_v1.py`
- Live proof: See above and JSON summary

---

## Author
- Automated by GitHub Copilot (GPT-4.1)
- Date: 2026-05-19
