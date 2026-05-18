# Button 1 Multisport Full Event Card Matchup Ingestion — Design & Implementation

## Slice
`button1-multisport-full-event-card-matchup-ingestion-v1`

## Status
LOCKED

## Goal
Upgrade Button 1 approved-source live feed ingestion from headline/sample matchup (1 per card) to full-card matchup ingestion for approved event cards and promoters.

---

## Hard Constraints
1. Do not fake matchups.
2. Do not invent undercard rows.
3. Do not weaken Gate 1.
4. Do not auto-save queue rows.
5. Do not auto-generate PDFs.
6. Do not auto-deliver.
7. Do not write learning/calibration.
8. Do not mutate Button 3.
9. Every matchup must carry event-level or matchup-level URL-backed provenance.
10. Missing/uncertain matchup rows must be marked `needs_review`, not `ready_to_save`.
11. If a source only exposes a partial card, label `card_completeness_status=partial_card` or `headline_only`.
12. If full-card extraction is unsupported, fail closed with clear `extraction_diagnostics`.

---

## Card Completeness Status Per Event

| Sport      | Event Name      | Before (matchups) | After (matchups) | card_completeness_status | extraction_method              |
|------------|-----------------|:-----------------:|:----------------:|--------------------------|-------------------------------|
| Boxing     | Joshua vs Dubois | 1                | 1                | `headline_only`          | `static_feed_headline_only`   |
| MMA        | UFC 300          | 1                | 1                | `headline_only`          | `static_feed_headline_only`   |
| Kickboxing | GLORY 100        | 1                | 1                | `headline_only`          | `static_feed_headline_only`   |
| Muay Thai  | ONE SAMURAI 1    | 2                | **15**           | `full_card_confirmed`    | `manual_verified_feed`        |

---

## New Required Event-Card Fields

All four events now carry:
- `card_completeness_status` — one of `full_card_confirmed`, `partial_card`, `headline_only`, `extraction_unsupported`, `needs_review`
- `matchup_count` — integer count of matchups in the feed
- `expected_matchup_count` — integer if known, `null` if unknown
- `extraction_method` — how matchup data was obtained
- `extraction_diagnostics` — human-readable reason for partial/unsupported status

All matchups now carry:
- `fighter_a`, `fighter_b`, `weight_class`, `bout_order`
- `ruleset` (Boxing/MMA/Kickboxing/Muay Thai)
- `title_fight` (true/false)
- `source_backed` (true/false)
- `source_url` (matchup-level or inherited from event)
- `provenance_status`
- `button2_readiness_status`
- `queue_save_eligible`
- `review_reason` (if not eligible)

---

## ONE SAMURAI 1 Full Card (15 Bouts)

| Order | Fighter A             | Fighter B               | Division   | Ruleset    | Title |
|-------|-----------------------|-------------------------|------------|------------|-------|
| 1     | Rodtang Jitmuangnon   | Takeru Segawa           | Flyweight  | Kickboxing | ✓     |
| 2     | Yuya Wakamatsu        | Avazbek Kholmirzaev     | Flyweight  | MMA        | ✓     |
| 3     | Nadaka                | Songchainoi Kiatsongrit | Atomweight | Muay Thai  | ✓     |
| 4     | Jonathan Haggerty     | Yuki Yoza               | Bantamweight | Kickboxing | ✓   |
| 5     | Marat Grigorian       | Kaito                   | Featherweight | Kickboxing | -  |
| 6     | Ayaka Miura           | Chihiro Sawada          | Atomweight | MMA        | -     |
| 7     | Hiroki Akimoto        | Taimu Hisai             | Bantamweight | Kickboxing | -  |
| 8     | Hiromi Wajima         | Ricardo Bravo           | Featherweight | Kickboxing | -  |
| 9     | Itsuki Hirata         | Ritu Phogat             | Atomweight | MMA        | -     |
| 10    | Tatsumitsu Wada       | Seiichiro Ito           | Flyweight  | MMA        | -     |
| 11    | Keito Yamakita        | Ryohei Kurosawa         | Strawweight | MMA       | -     |
| 12    | Shimon Yoshinari      | Johan Ghazali           | Flyweight  | Muay Thai  | -     |
| 13    | Toma Kuroda           | Toki Tamaru             | Atomweight | Kickboxing | -     |
| 14    | Hyu                   | Taiki Naito             | Flyweight  | Kickboxing | -     |
| 15    | Kanata Nagai          | Atsubo Kambe            | Bantamweight | MMA      | -     |

Source: muaythairecords.com/events/one-samurai-1 (tier B, requires secondary confirmation)
All ONE SAMURAI 1 matchups: `queue_save_eligible=false`, `review_reason=secondary_confirmation_required`

---

## Boxing / MMA / Kickboxing (Partial Card / Headline Only)

These events are future cards where only the headline bout is confirmed from the static feed. Live extraction from matchroomboxing.com, ufc.com, and glorykickboxing.com is not yet supported. Each is marked:
- `card_completeness_status: "headline_only"`
- `extraction_method: "static_feed_headline_only"`
- `extraction_diagnostics: <descriptive text>`
- `expected_matchup_count: null`

---

## Source Strategy Compliance

| Sport      | Primary Source                      | Tier | Secondary Confirmation | Status     |
|------------|-------------------------------------|------|------------------------|------------|
| Boxing     | matchroomboxing.com                 | A    | Not required           | headline_only |
| MMA        | ufc.com/event/                      | A    | Not required           | headline_only |
| Kickboxing | glorykickboxing.com/events/         | A    | Not required           | headline_only |
| Muay Thai  | muaythairecords.com/events/         | B    | Required               | full_card_confirmed |

---

## Dashboard Changes

`operator_dashboard/templates/index.html`:
- `buildEventCardAndMatchupSelectorModel()`: Expanded to read nested `row.matchups[]` and render each as a matchup row under the event card (with deduplication).
- `card_completeness_status` now captured from row and included in event card model.
- `renderButton1EventCardSelector()`: Event header now displays **Card Completeness** field.

---

## Files Changed

- `ops/approved_sources/button1_live_event_source_rows.json` — Added completeness fields to all 4 events; expanded ONE SAMURAI 1 from 2 to 15 matchups
- `operator_dashboard/templates/index.html` — JS: nested matchup expansion + card_completeness_status display
- `operator_dashboard/test_button1_multisport_full_event_card_matchup_ingestion_v1.py` — NEW: 15 focused tests
- `docs/button1_multisport_full_event_card_matchup_ingestion_v1.md` — NEW: this document
- `ops/release_checks/button1_multisport_full_event_card_matchup_ingestion_v1/full_card_matchup_ingestion_summary.json` — NEW: release evidence

---

## Governance Result

- Gate 1 remains preview-only. No writes executed.
- No PDF generation. No auto-delivery. No learning/calibration.
- Button 3 untouched.
- All ONE SAMURAI 1 matchups blocked from queue save due to tier B secondary confirmation requirement.
- All Boxing/MMA/Kickboxing headline bouts remain `queue_save_eligible: true` (tier A, no secondary confirmation required).
