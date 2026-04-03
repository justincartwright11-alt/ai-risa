# Routing Catalog Chain Audit

## Source files

- ops\model_adjustments\model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_index.json
- ops\model_adjustments\model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_directory.json
- ops\model_adjustments\model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_locator.json
- ops\model_adjustments\model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_register.json
- ops\model_adjustments\model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_ledger.json
- ops\model_adjustments\model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_manifest.json

## Source record counts

- routing_catalog_index: 3
- routing_catalog_directory: 3
- routing_catalog_locator: 3
- routing_catalog_register: 3
- routing_catalog_ledger: 3
- routing_catalog_manifest: 3

**all_checks_pass:** True

## Checks

| check_name | result |
|---|---|
| layer_record_count_parity_pass | True |
| audit_record_count_matches_manifest_pass | True |
| exact_once_lineage_pass | True |
| source_order_preserved_pass | True |
| deterministic_suffix_alignment_pass | True |
| terminal_manifest_coverage_pass | True |

## Audit records

| routing_catalog_chain_audit_id | audit_position | routing_catalog_index_id | routing_catalog_directory_id | routing_catalog_locator_id | routing_catalog_register_id | routing_catalog_ledger_id | routing_catalog_manifest_id | lineage_chain_complete | source_order_preserved | deterministic_suffix_alignment | exact_once_lineage | lineage_source_layer | lineage_source_file | lineage_source_record_id |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| resolution-wave-packet-review-session-routing-catalog-chain-audit-0001 | 1 | resolution-wave-packet-review-session-routing-catalog-index-0001 | resolution-wave-packet-review-session-routing-catalog-directory-0001 | resolution-wave-packet-review-session-routing-catalog-locator-0001 | resolution-wave-packet-review-session-routing-catalog-register-0001 | resolution-wave-packet-review-session-routing-catalog-ledger-0001 | resolution-wave-packet-review-session-routing-catalog-manifest-0001 | True | True | True | True | routing_catalog_manifest | ops\model_adjustments\model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_manifest.json | resolution-wave-packet-review-session-routing-catalog-manifest-0001 |
| resolution-wave-packet-review-session-routing-catalog-chain-audit-0002 | 2 | resolution-wave-packet-review-session-routing-catalog-index-0002 | resolution-wave-packet-review-session-routing-catalog-directory-0002 | resolution-wave-packet-review-session-routing-catalog-locator-0002 | resolution-wave-packet-review-session-routing-catalog-register-0002 | resolution-wave-packet-review-session-routing-catalog-ledger-0002 | resolution-wave-packet-review-session-routing-catalog-manifest-0002 | True | True | True | True | routing_catalog_manifest | ops\model_adjustments\model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_manifest.json | resolution-wave-packet-review-session-routing-catalog-manifest-0002 |
| resolution-wave-packet-review-session-routing-catalog-chain-audit-0003 | 3 | resolution-wave-packet-review-session-routing-catalog-index-0003 | resolution-wave-packet-review-session-routing-catalog-directory-0003 | resolution-wave-packet-review-session-routing-catalog-locator-0003 | resolution-wave-packet-review-session-routing-catalog-register-0003 | resolution-wave-packet-review-session-routing-catalog-ledger-0003 | resolution-wave-packet-review-session-routing-catalog-manifest-0003 | True | True | True | True | routing_catalog_manifest | ops\model_adjustments\model_adjustment_release_resolution_wave_packet_review_session_routing_catalog_manifest.json | resolution-wave-packet-review-session-routing-catalog-manifest-0003 |
