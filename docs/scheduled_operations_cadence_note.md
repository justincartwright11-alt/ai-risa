# Scheduled Operations Cadence Note

**Effective Date:** April 18, 2026

## Operating Mode
- Controlled routine use at limited scale is now the active operating mode.
- Only the three validated request shapes (happy-path, blocked, failed_precondition) are permitted.
- All operations are governed by docs/runtime_release_manifest.md and docs/operator_release_go_no_go_note.md.
- docs/live_release_window_log.md remains the sole operational record.

## Cadence
- Controlled release windows will be scheduled at regular intervals (e.g., daily or weekly) as determined by operator needs and system load.
- Each window will follow the same discipline: log all actions, outcomes, and decisions; stop and classify on any deviation.
- No scope expansion or new request shapes without explicit operator signoff and new validation windows.

## Authority
- All operational decisions are governed by the manifest and go/no-go note.
- Any deviation triggers maintenance/hotfix or rollback, never ad hoc adjustment.

---

*This note formalizes the transition from proof windows to scheduled controlled operations.*
