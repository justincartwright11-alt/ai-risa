# AI-RISA Visual Intelligence Research Application Roadmap (v1)

## Purpose
Convert the locked research-and-implications engine into a prioritized roadmap of future report, dashboard, and PDF upgrade slices.

This slice is docs-only.

## Core Rule
Research must become implementation rules before any visual or PDF build begins.
No renderer or dashboard runtime changes are allowed in this slice.

## Upstream Locked Inputs
- ai-risa-research-and-implications-engine-v1 (555cd88)
- button2-dossier-handoff-report-context-final-handoff-v1 (9aa11ae)

## Planning Constraints
- Preserve preview-only and Gate 2 governance constraints.
- Preserve zero-write behavior in preview pathways.
- Keep all runtime/UI/PDF generation code unchanged in this roadmap slice.
- Define acceptance-first slices for future implementation.

## Prioritized Application Sequence

### Phase 1: Report Intelligence Core
Focus: fight footage research to improve report intelligence quality before visual polish.

Planned slices:
1. button2-report-intelligence-fight-footage-principles-design-v1
2. button2-report-intelligence-fight-footage-acceptance-rules-v1
3. button2-report-intelligence-fight-footage-preview-wire-v1

Expected output:
- Stronger tactical and matchup inference rules.
- Better evidence-linked narrative structure.
- Acceptance tests for intelligence quality and consistency.

### Phase 2: PDF Visual Language
Focus: broadcast graphics research translated into PDF visual hierarchy and storytelling.

Planned slices:
1. button2-pdf-visual-language-broadcast-graphics-design-v1
2. button2-pdf-visual-language-broadcast-graphics-acceptance-rules-v1
3. button2-pdf-visual-language-preview-spec-v1

Expected output:
- Clear information hierarchy for key report signals.
- Broadcast-grade callout and emphasis patterns.
- Visual acceptance rules before renderer changes.

### Phase 3: Briefing Structure and Decision Support
Focus: military/intelligence briefing research for report structure and operator decision flow.

Planned slices:
1. button2-report-briefing-structure-design-v1
2. button2-report-briefing-structure-acceptance-rules-v1
3. button2-report-briefing-preview-composition-v1

Expected output:
- Executive-summary-to-detail flow.
- Confidence and uncertainty communication standards.
- Decision-ready section ordering rules.

### Phase 4: Dashboard and Telemetry Principles
Focus: Bloomberg and F1 dashboard research to define dashboard principles for future upgrades.

Planned slices:
1. button2-dashboard-telemetry-principles-design-v1
2. button2-dashboard-telemetry-acceptance-rules-v1
3. button2-dashboard-preview-principles-pack-v1

Expected output:
- Scan-first metrics and telemetry pattern standards.
- Trend and state communication rules.
- Acceptance criteria for dashboard readability and actionability.

### Phase 5: Scouting and Dossier Depth
Focus: professional scouting-report research for fighter profile and dossier upgrades.

Planned slices:
1. fighter-dossier-scouting-intelligence-design-v1
2. fighter-dossier-scouting-intelligence-acceptance-rules-v1
3. fighter-dossier-scouting-preview-upgrade-v1

Expected output:
- Richer fighter intelligence framing.
- Opponent-interaction and matchup-depth standards.
- Dossier quality acceptance gates.

## Cross-Phase Acceptance Rule Framework
Every future implementation slice must define testable acceptance rules for:
- Intelligence quality and traceability.
- Visual hierarchy correctness.
- Safety and governance invariants.
- Preview-only vs execution path boundaries.
- Gate 2 approval separation.

Required invariant checks:
- No auto-generation from preview pathways.
- No auto-export/PDF/delivery behavior.
- No write-path activation in preview contexts.
- No Gate 2 bypass.

## Implementation Readiness Gates
Before any renderer, layout, or PDF generation code changes begin:
1. Design slice locked for that phase.
2. Acceptance rules slice locked for that phase.
3. Preview specification slice locked for that phase.
4. Governance and safety invariants restated and testable.

## Out of Scope (This Slice)
- Renderer implementation changes
- Dashboard runtime changes
- Button 1 runtime changes
- Button 2 runtime/layout/PDF changes
- Button 3 learning/calibration changes
- Database changes
- PDF generation changes

## Next Recommended Slice
- button2-report-intelligence-fight-footage-principles-design-v1
- Purpose: begin Phase 1 design by translating fight footage research into report intelligence principles and acceptance-ready rules.

## Final Verdict
The roadmap is now locked to ensure research is applied as structured implementation rules before any visual, renderer, dashboard, or PDF build work proceeds.