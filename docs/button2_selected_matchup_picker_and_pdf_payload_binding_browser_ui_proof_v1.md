# button2-selected-matchup-picker-and-pdf-payload-binding-browser-ui-proof-v1

## Scope
Proof-only slice confirming the locked backend repair through the actual dashboard UI click path.

Baseline under proof:
- Slice: `button2-selected-matchup-picker-and-pdf-payload-binding-repair-v1`
- Commit: `6fa6097`
- Tag: `button2-selected-matchup-picker-and-pdf-payload-binding-repair-v1`

## Objective
From the live dashboard UI, prove the operator can:
1. Select one queued matchup row in Button 2.
2. Generate report A.
3. Select a different queued matchup row.
4. Generate report B.
5. Open generated PDFs.
6. Confirm visible/content-extracted PDF payload changes by selected row.

## Environment
- Server: Flask app from `operator_dashboard.app`
- Port used for proof: `http://127.0.0.1:5051`
- Output root: `C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports`

## UI Flow Evidence
### 1) Button 2 panel showed selectable queued rows
Rows displayed in panel:
- Rico Verhoeven vs Tariq Osaro
  - Event: GLORY 100
  - Source: https://www.glorykickboxing.com/events/glory-100
  - Readiness: ready_for_button2_preview
  - matchup_id: glory100_rico_tariq
- Nadaka Yoshinari vs Songchainoi Kiatsongrit
  - Event: ONE Samurai 1
  - Source: https://www.onefc.com/events/one-samurai-1
  - Readiness: ready_for_button2_preview
  - matchup_id: onesamurai_nadaka_songchainoi

### 2) Generate after selecting first row
Selected row: Rico Verhoeven vs Tariq Osaro

Generated:
- Output path: `C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports\rico_verhoeven_vs_tariq_osaro_glory_100_premium_20260519T081349Z_38b7a3ec0f39.pdf`
- Open route link emitted in UI and opened: `/api/button2/generated-report/open?filename=rico_verhoeven_vs_tariq_osaro_glory_100_premium_20260519T081349Z_38b7a3ec0f39.pdf`

### 3) Generate after switching to second row
Selected row: Nadaka Yoshinari vs Songchainoi Kiatsongrit

Generated:
- Output path: `C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports\nadaka_yoshinari_vs_songchainoi_kiatsongrit_one_samurai_1_premium_20260519T081401Z_f9a5017743bc.pdf`
- Open route link emitted in UI and opened: `/api/button2/generated-report/open?filename=nadaka_yoshinari_vs_songchainoi_kiatsongrit_one_samurai_1_premium_20260519T081401Z_f9a5017743bc.pdf`

## Content-Difference Validation
Extracted text from both generated PDFs and compared:
- file A contains fighter/event for Rico/Tariq + GLORY 100
- file B contains fighter/event for Nadaka/Songchainoi + ONE Samurai 1
- file B does not contain stale Anthony Joshua + Daniel Dubois pair
- full extracted text differs between A and B

Validation result payload:
```json
{
  "a_exists": true,
  "b_exists": true,
  "a_has_rico": true,
  "a_has_event": true,
  "b_has_nadaka": true,
  "b_has_event": true,
  "b_has_joshua_dubois": false,
  "texts_different": true,
  "a_len": 9485,
  "b_len": 9639
}
```

## Governance Flags (UI result block)
For both generations, UI status reported:
- Delivery performed: No
- External API delivery performed: No
- Queue write performed: No
- Learning apply performed: No
- Calibration write performed: No
- Button 3 mutation performed: No

## Verdict
PASS. Browser UI proof confirms selected-matchup switching in Button 2 drives different generated PDF content, open route points to exact current output filename, and stale hard-bound Joshua/Dubois content is not present for a non-Joshua selected row.
