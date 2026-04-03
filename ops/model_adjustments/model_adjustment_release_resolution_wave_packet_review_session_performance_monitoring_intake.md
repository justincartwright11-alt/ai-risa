# v26.0 Controlled Release Resolution Wave Packet Review Session Performance Monitoring Intake

**Source files:**

- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_closeout.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_execution_evidence.json

**Intake record:**

performance_monitoring_intake_id | monitored_family | baseline_run_reference | monitoring_metrics | acceptable_ranges | alert_conditions | evidence_artifact | review_interval | stop_condition | lineage_source_layer | lineage_source_file | lineage_source_record_id
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---
resolution-wave-packet-review-session-performance-monitoring-intake-0001 | v25.0-v25.3-controlled-release-resolution-wave-packet-review-session-live-event-family | resolution-wave-packet-review-session-live-event-closeout-0001 | event_completion_time, incident_rate, deliverable_accuracy | {"event_completion_time": "< 2 hours", "incident_rate": "0%", "deliverable_accuracy": ">= 99%"} | incident_rate > 0%, deliverable_accuracy < 99% | resolution-wave-packet-review-session-live-event-execution-evidence-0001 | per event | 3 consecutive failures | live_event_closeout | ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_live_event_closeout.json | resolution-wave-packet-review-session-live-event-closeout-0001
