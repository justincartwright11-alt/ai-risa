# AI-RISA v1 Operator Prompt Pack

These are the locked v1 prompts for all governed AI-RISA operations.

---

## 1. Governed Pre-Event Cycle

```text
Run the governed AI-RISA pre-event cycle for this event.

Event ID: [event_id]
Manifest Path: [full_manifest_path]

Tasks:
1. Load the manifest
2. Refresh or validate all fighter profiles
3. Run the full event batch
4. Generate premium, broadcast, and betting outputs
5. Export all PDFs
6. Validate artifacts through the release gate
7. Write:
   - pre_event_cycle_result.json
   - batch_output.json
   - release_gate.json

Rules:
- Stop immediately on any failed stage
- Do not guess missing artifact paths
- Use only real batch output for expected_report_ids
- Return a final PASS/FAIL result

Output format:
- event_id
- fighter_refresh_status
- batch_run_status
- expected_report_ids
- release_gate_status
- release_ready
- failed_stage
- errors
```

---

## 2. Premium Fight Report

```text
Generate a full AI-RISA premium report for this matchup.

Fight:
[Fighter A] vs [Fighter B]
Sport/Ruleset: [boxing / MMA / kickboxing / Muay Thai]
Event: [event name]
Mode: premium

Use the core AI-RISA lenses:
- decision structure
- energy use
- fatigue failure points
- mental condition
- collapse triggers

Required sections:
1. Fight Intelligence Summary
2. Fighter Architecture
3. Round Flow Breakdown
4. Tactical Dominance Map
5. Scorecard Probability
6. Stoppage and Collapse Model
7. Corner Strategy
8. Final Verdict

Output should be PDF-ready and aligned with premium_template_v1.
```

---

## 3. Broadcast Brief

```text
Generate an AI-RISA broadcast brief for this matchup.

Fight:
[Fighter A] vs [Fighter B]
Mode: broadcast

Keep it one-page, commentary-ready, and concise.

Include:
- headline outcome
- opening phase control
- mid-fight shift
- key collapse trigger
- one tactical note for each fighter
- one scorecard storyline
- one stoppage storyline if live

Keep language sharp, fast, and readable on air.
```

---

## 4. Betting Brief

```text
Generate an AI-RISA betting brief for this matchup.

Fight:
[Fighter A] vs [Fighter B]
Mode: betting

Keep it compact and probability-first.

Include:
- model lean
- win probability
- most likely card
- alternate card
- split-decision risk
- stoppage window
- upset path
- confidence note

Keep it one-page and decision-focused.
```

---

## 5. Governed Live-Event Cycle

```text
Run the governed AI-RISA live-event cycle for this live round input.

Event ID: [event_id]
Matchup ID: [matchup_id]
Live Input Path: [full_json_path]

Tasks:
1. Load live round input
2. Validate required fields
3. Save live update JSON
4. Generate live delta report
5. Write live_event_cycle_result.json

Required live fields:
- event_id
- matchup_id
- round
- event_time_ref
- control_owner
- momentum_shift
- scorecard_path
- corner_advice_delta
- event_log

Rules:
- Stop immediately on validation or save failure
- Do not invent missing round data
- Return final PASS/FAIL
```

---

## 6. Governed Post-Event Cycle

```text
Run the governed AI-RISA post-event cycle for this event.

Event ID: [event_id]
Results Path: [full_results_json_path]

Tasks:
1. Load official results
2. Save per-fight result objects
3. Generate calibration objects
4. Generate calibration batch
5. Generate proposal if meaningful misses exist
6. Write post_event_cycle_result.json

Required calibration fields:
- winner_correct
- method_correct
- scorecard_shape_correct
- margin_error
- error_class.primary
- error_class.secondary

Rules:
- If there are no meaningful misses, skip proposal and state the reason explicitly
- Stop immediately on failure
- Return final PASS/FAIL
```

---

## 7. Release Gate

```text
Run the AI-RISA release gate for this event.

Event ID: [event_id]
Batch Output Path: [full_batch_output_json_path]

Validate:
- all expected reports exist
- all expected PDFs exist
- artifact paths come from batch_output.json, not guessed paths
- blockers
- major issues
- warnings
- release_ready

Output:
- status
- release_ready
- failed_stage
- errors
```

---

## 8. Fighter Profile Generation / Refresh

```text
Create or refresh a provisional AI-RISA fighter profile for this fighter.

Fighter: [fighter name]
Sport: [sport]
Division: [division]
Stance: [stance if known]

Build:
- style_archetype
- biomechanics
- offense
- defense
- ring_iq
- conditioning
- mental
- metadata

Rules:
- conservative first-pass values
- no blank fields
- mark as provisional
- include data_confidence
- include source_count
- include notes: provisional event-run starter profile
```

---

## 9. Event Manifest Creation

```text
Create an AI-RISA event manifest for this card.

Event ID: [event_id]
Event Name: [event name]
Date: [date]
Location: [location]
Promotion: [promotion]

Fights:
1. [fighter_a] vs [fighter_b] — [division] — [sport/ruleset]
2. [fighter_a] vs [fighter_b] — [division] — [sport/ruleset]

Return a valid event_manifest.yaml with normalized fight entries for the AI-RISA pipeline.
```

---

## 10. Feedback Review

```text
Review AI-RISA feedback for this report or event.

Target:
[report_id or event_id]

Group feedback by:
- engine
- template
- audience-format

Classify each issue as:
- cosmetic
- content
- model-affecting

Output:
- repeated issues
- severity
- recommended action
- whether this should wait for v1.1 review
```

---

## 11. Calibration Miss Review

```text
Review calibration misses for this event.

Event ID: [event_id]

Tasks:
1. Load calibration batch
2. Identify all misses
3. Group by error_class.primary
4. Separate model issues from presentation issues
5. State whether evidence is strong enough for a v1.1 proposal

Output:
- total misses
- grouped miss types
- repeated patterns
- recommended action
```

---

## 12. Daily Operator Prompt

```text
Run today’s AI-RISA operator workflow.

For each active event:
1. Check manifest status
2. Check fighter profile readiness
3. Run governed pre-event cycle if not already complete
4. If event is live, process any live round updates
5. If official results exist, run governed post-event cycle
6. Summarize:
   - ready events
   - blocked events
   - live events
   - completed events
   - required operator actions
```

---

# Three Core Day-to-Day Prompts

## A. Pre-Event

```text
Run the governed AI-RISA pre-event cycle for this event using the manifest at [path]. Refresh fighters, run the full event batch, export premium/broadcast/betting PDFs, validate through the release gate, and return a final PASS/FAIL with errors if any.
```

## B. Live Event

```text
Run the governed AI-RISA live-event cycle for this live round input at [path]. Validate input, save live update, generate delta report, write live_event_cycle_result.json, and return PASS/FAIL.
```

## C. Post-Event

```text
Run the governed AI-RISA post-event cycle for event [event_id] using results at [path]. Save results, generate calibration batch, generate a proposal if meaningful misses exist, write post_event_cycle_result.json, and return PASS/FAIL.
```
