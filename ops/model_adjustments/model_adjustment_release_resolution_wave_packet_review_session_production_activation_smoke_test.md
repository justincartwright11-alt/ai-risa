# v19.1 Production Activation Smoke Test

- record_type: model_adjustment_release_resolution_wave_packet_review_session_production_activation_smoke_test
- source_file: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_intake.json
- source_record_count: 0
- record_count: 1
- production_activation_smoke_test_pass: False
- checks: {'production_activation_intake_present_pass': False, 'external_consumer_handoff_present_pass': False, 'production_activation_readiness_pass': False, 'downstream_activation_path_pass': False, 'deterministic_output_pass': False}

## Records

- production_activation_smoke_test_id: resolution-wave-packet-review-session-production-activation-smoke-test-0001
- smoke_test_position: 1
- production_activation_intake_id: resolution-wave-packet-review-session-production-activation-intake-0001
- production_activation_smoke_test_pass: True
- lineage_source_layer: production_activation_intake
- lineage_source_file: ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_production_activation_intake.json
- lineage_source_record_id: resolution-wave-packet-review-session-production-activation-intake-0001
