# v16.4 Controlled Release Resolution Wave Packet Review Session Consumer Audit

## Source Files
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_intake.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_queue.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_dispatch.json
- ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_batch.json

## Checks
- layer_record_count_parity_pass: true
- audit_record_count_matches_batch_pass: true
- exact_once_lineage_pass: true
- source_order_preserved_pass: true
- deterministic_suffix_alignment_pass: true
- terminal_batch_coverage_pass: true
- all_checks_pass: true

## Audit Table
consumer_audit_id | audit_position | consumer_intake_id | consumer_queue_id | consumer_dispatch_id | consumer_batch_id | lineage_chain_complete | source_order_preserved | deterministic_suffix_alignment | exact_once_lineage | lineage_source_layer | lineage_source_file | lineage_source_record_id
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---
resolution-wave-packet-review-session-consumer-audit-0001 | 1 | resolution-wave-packet-review-session-consumer-intake-0001 | resolution-wave-packet-review-session-consumer-queue-0001 | resolution-wave-packet-review-session-consumer-dispatch-0001 | resolution-wave-packet-review-session-consumer-batch-0001 | true | true | true | true | consumer_batch | ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_consumer_batch.json | resolution-wave-packet-review-session-consumer-batch-0001
