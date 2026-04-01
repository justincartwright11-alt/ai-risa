
# AI-RISA Operator Cheat Sheet

## Quick Start

```
Run AI-RISA full-auto for <fighter / matchup / event> using the <report type> report.

Report types:
Fighter/Trainer
Promoter
Broadcast
Premium Fan
```

# AI-RISA Best Prompts Cheat Sheet

## Master Operator Prompt
Use this when you want AI-RISA to run without drifting into redesign.

```text
Act as a strict AI-RISA operator.

Use the existing full-auto pipeline and current local AI-RISA structure.
Do not redesign anything.
Do not refactor unless a real defect appears.
Do not ask unnecessary follow-up questions.
Only ask which report type I want if it is not already specified.

Report types:
- Fighter/Trainer
- Promoter
- Broadcast
- Premium Fan

Always do the full workflow automatically:
- locate or create needed fighter/matchup/event data
- run the correct AI-RISA mode
- write outputs to the normal folders
- report the files created/updated
- report the exact rerun command
- report the reconciliation command

If something fails:
- diagnose the first real boundary
- apply the smallest valid fix only
- rerun and confirm
```

1. Single Fighter Dossier
Run AI-RISA in full-auto fighter mode for <fighter name> using the <report type> report.

Use the existing full-auto pipeline.
Create or update the fighter file if needed.
Generate the dossier and write it to the normal AI-RISA reports location.

Return only:
1. files created or updated
2. output location
3. exact rerun command
4. a short summary of:
	- style
	- decision structure
	- energy use
	- fatigue failure points
	- mental condition
	- collapse triggers

Example
Run AI-RISA in full-auto fighter mode for Tim Tszyu using the Fighter/Trainer report.


2. Fighter A vs Fighter B
Run AI-RISA in full-auto matchup mode for <fighter A> vs <fighter B> using the <report type> report.

Use the existing full-auto pipeline.
Create or update both fighter files and the matchup file if needed.
Run the matchup automatically and write the prediction/report outputs.

Return only:
1. files created or updated
2. output location
3. exact rerun command
4. the result summary:
	- predicted winner
	- method tendency
	- confidence if available
	- main tactical edge
	- round-flow projection

Example
Run AI-RISA in full-auto matchup mode for Tim Tszyu vs Denis Nurja using the Fighter/Trainer report.


3. Full Event Card
Run AI-RISA in full-auto event mode for <event slug or event name> using the <report type> report.

Use the existing full-auto pipeline.
Create or update any missing fighter, matchup, and event data.
Use the existing runner if present; create the smallest valid runner only if needed.
Run the full card automatically.
Write all prediction outputs and the event summary.

Return only:
1. files created or updated
2. scripts run
3. output locations
4. which fights passed
5. exact rerun command
6. exact reconciliation command

Example
Run AI-RISA in full-auto event mode for boxing_wollongong_2026_04_05 using the Fighter/Trainer report.


4. Premium Report Packaging
Turn the latest AI-RISA outputs for <event or matchup> into a premium <report type> report pack.

Use the current AI-RISA report structure.
Keep the tone premium, analytical, and tactical.
Do not use betting-hype language.

Include:
- cover page
- executive summary
- fight-by-fight breakdowns
- event-wide conclusions
- disclaimer

For each fight include:
- predicted winner
- method tendency
- decision structure
- energy use
- fatigue failure points
- mental condition
- collapse triggers
- main tactical edge
- round-flow projection
- audience-appropriate guidance

Example
Turn the latest Wollongong AI-RISA outputs into a premium Fighter/Trainer report pack.


5. Reconciliation
Run AI-RISA reconciliation now.

Use:
python C:/ai_risa_data/run_reconciliation_trend_report.py

Return only:
1. whether it passed
2. files created or updated
3. output locations
4. matched count
5. unmatched count
6. conflict count
7. whether anything requires review


6. Full-Auto Everything Prompt
Use AI-RISA full-auto mode and do everything automatically for this assignment.

Assignment:
<insert fighter, matchup, or event>

Report type:
<insert one: Fighter/Trainer, Promoter, Broadcast, Premium Fan>

Rules:
- detect whether this is fighter, matchup, or event mode
- use the existing full-auto pipeline
- create or update only what is missing
- do not redesign anything
- do not ask extra questions
- run the workflow end to end
- write outputs to the normal AI-RISA folders
- report exact rerun and reconciliation commands

Return only:
1. mode used
2. files created or updated
3. output locations
4. pass/fail
5. key result summary
6. rerun command
7. reconciliation command


7. Latest Output Check
Show me the latest AI-RISA outputs for the most recent run.

Check:
- C:/ai_risa_data/predictions/
- C:/ai_risa_data/reports/

Return only:
1. latest files
2. timestamps
3. which workflow likely created them
4. which file I should open first


8. Maintenance Check
Perform a read-only AI-RISA maintenance check.

Do not change code.
Do not refactor.
Do not redesign.
Do not change schemas or thresholds.

Check:
- latest outputs
- row counts if relevant
- whether expected artifacts were emitted
- whether anything looks broken or implausible

Return only:
- status
- anomalies
- whether action is required


9. Failure / Debug Prompt
Debug this AI-RISA failure with the smallest possible fix.

Rules:
- diagnose first
- find the first real failing boundary
- do not redesign anything
- apply the smallest valid fix only if necessary
- rerun and confirm

Return only:
1. root cause
2. exact file involved
3. minimal fix
4. rerun result


Fastest Everyday Prompts
Single Fighter
Run AI-RISA full-auto for Tim Tszyu using the Fighter/Trainer report.

Matchup
Run AI-RISA full-auto for Tim Tszyu vs Denis Nurja using the Fighter/Trainer report.

Event Card
Run AI-RISA full-auto for boxing_wollongong_2026_04_05 using the Fighter/Trainer report.

Package Report
Turn the latest Wollongong AI-RISA outputs into a premium Fighter/Trainer report pack.

Reconciliation
Run AI-RISA reconciliation now and summarize matched, unmatched, and conflicts.


Default Report-Type Prompts
Fighter / Trainer
Run AI-RISA full-auto for <assignment> using the Fighter/Trainer report.

Promoter
Run AI-RISA full-auto for <assignment> using the Promoter report.

Broadcast
Run AI-RISA full-auto for <assignment> using the Broadcast report.

Premium Fan
Run AI-RISA full-auto for <assignment> using the Premium Fan report.


Final Rule
Use VS Code AI chat to run AI-RISA locally.
Use ChatGPT to rewrite outputs into premium deliverables.
Only required choice: report type.
Everything else should run automatically.

## Core Commands

### 1. Single Fighter Dossier
```
python C:/ai_risa_data/run_full_auto_pipeline.py --mode fighter --fighter "<Fighter Name>" --report "<Report Type>"
```
**Example:**
```
python C:/ai_risa_data/run_full_auto_pipeline.py --mode fighter --fighter "Tim Tszyu" --report "Fighter/Trainer"
```

### 2. Fighter vs Fighter (Head-to-Head)
```
python C:/ai_risa_data/run_full_auto_pipeline.py --mode matchup --fighter-a "<Fighter A>" --fighter-b "<Fighter B>" --report "<Report Type>"
```
**Example:**
```
python C:/ai_risa_data/run_full_auto_pipeline.py --mode matchup --fighter-a "Tim Tszyu" --fighter-b "Denis Nurja" --report "Fighter/Trainer"
```

### 3. Full Event Card
```
python C:/ai_risa_data/run_full_auto_pipeline.py --mode event --event <event_slug> --report "<Report Type>"
```
**Example:**
```
python C:/ai_risa_data/run_full_auto_pipeline.py --mode event --event boxing_wollongong_2026_04_05 --report "Fighter/Trainer"
```

### 4. Reconciliation (Post-Event)
```
python C:/ai_risa_data/run_reconciliation_trend_report.py
```

## Report Types
- Fighter/Trainer
- Promoter
- Broadcast
- Premium Fan

## Output Locations
- Fighters: C:/ai_risa_data/fighters/
- Matchups: C:/ai_risa_data/matchups/
- Events: C:/ai_risa_data/events/
- Predictions: C:/ai_risa_data/predictions/
- Reports: C:/ai_risa_data/reports/

---
**Tip:** Only the report type is required as a human input. All other steps are fully automated.
