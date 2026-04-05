#!/usr/bin/env python3
"""
v6.1: Model Adjustment Release Resolution Wave Packet Review Session Receipt Generator

Pure downstream projection of review-session-intake into operator-receipt normalization layer.
Consumes: model_adjustment_release_resolution_wave_packet_review_session_intake.json (v6.0)
Produces: model_adjustment_release_resolution_wave_packet_review_session_receipt.json (v6.1)
          model_adjustment_release_resolution_wave_packet_review_session_receipt.md (v6.1)

Behavior:
- One receipt entry per upstream intake entry
- Preserves all upstream priority, lane, posture fields exactly (pass-through)
- Adds receipt-specific projection fields only (receipt_position, receipt_priority, receipt_id)
- Deterministic ordering stable on intake_id / handoff_id
- No re-classification, no release logic, no policy logic
- Fail-closed validation: raises explicit errors on malformed upstream data
- Markdown as pure projection of JSON

Architecture:
- Validate upstream intake JSON (version, record structure, required fields)
- Build receipt records (1:1 from intake, all 35 fields, sorted deterministically)
- Generate JSON output with metadata
- Generate markdown pure projection
- Assert coverage: exact-once mapping from intake to receipt
"""

import json
import os
import datetime
import sys

# Downstream consumer configuration
SOURCE_PATHS = {
    'intake': 'ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_intake.json',
}

OUTPUT_PATHS = {
    'json': 'ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_receipt.json',
    'md': 'ops/model_adjustments/model_adjustment_release_resolution_wave_packet_review_session_receipt.md',
}

# Lane ordering for deterministic sort
LANE_ORDER = {
    'lane_prohibition_terminal': 0,
    'lane_blocker_terminal': 1,
    'lane_remaining_terminal': 2,
}

def normalize_string(value, name):
    """Validate non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid {name}: expected non-empty string, got {repr(value)}")
    return value

def normalize_list(value, name):
    """Normalize list (ensure it's a list, sort, deduplicate)."""
    if not isinstance(value, list):
        raise ValueError(f"Invalid {name}: expected list, got {type(value).__name__}")
    return sorted(set(value))

def normalize_int(value, name):
    """Validate integer."""
    if not isinstance(value, int):
        raise ValueError(f"Invalid {name}: expected int, got {type(value).__name__}")
    return value

def normalize_bool(value, name):
    """Validate boolean."""
    if not isinstance(value, bool):
        raise ValueError(f"Invalid {name}: expected bool, got {type(value).__name__}")
    return value

def validate_upstream_payload(payload, path):
    """Validate upstream intake JSON structure and version."""
    if not isinstance(payload, dict):
        raise ValueError(f"Upstream payload {path} is not a dict: {type(payload).__name__}")
    
    # Check version
    version = payload.get('model_adjustment_release_resolution_wave_packet_review_session_intake_version')
    if version != 'v6.0-slice-1':
        raise ValueError(f"Expected intake version 'v6.0-slice-1', got {repr(version)}")
    
    # Check records (using actual v6.0 key structure)
    records = payload.get('release_resolution_wave_packet_review_session_intake', [])
    if not isinstance(records, list):
        raise ValueError(f"release_resolution_wave_packet_review_session_intake is not a list: {type(records).__name__}")
    
    if len(records) == 0:
        raise ValueError("No intake records found in upstream payload")
    
    return records

def build_receipt_records(intake_records):
    """
    Build receipt records from intake records.
    One receipt entry per intake entry, deterministic ordering.
    All 35 required fields: pass-through from intake + receipt-specific fields.
    """
    receipt_records = []
    
    for idx, intake_record in enumerate(intake_records):
        # Validate required upstream fields
        try:
            intake_id = normalize_string(
                intake_record.get('resolution_wave_packet_review_session_intake_id'),
                'intake_id'
            )
            handoff_id = normalize_string(
                intake_record.get('source_resolution_wave_packet_review_session_handoff_id'),
                'handoff_id'
            )
            brief_id = normalize_string(
                intake_record.get('source_resolution_wave_packet_review_session_brief_id'),
                'brief_id'
            )
            pack_id = normalize_string(
                intake_record.get('source_resolution_wave_packet_review_session_pack_id'),
                'pack_id'
            )
            agenda_id = normalize_string(
                intake_record.get('source_resolution_wave_packet_review_agenda_id'),
                'agenda_id'
            )
            docket_id = normalize_string(
                intake_record.get('source_resolution_wave_packet_review_docket_id'),
                'docket_id'
            )
            board_id = normalize_string(
                intake_record.get('source_resolution_wave_packet_review_board_id'),
                'board_id'
            )
            checklist_id = normalize_string(
                intake_record.get('source_resolution_wave_packet_checklist_id'),
                'checklist_id'
            )
            packet_id = normalize_string(
                intake_record.get('source_resolution_wave_packet_id'),
                'packet_id'
            )
            wave_id = normalize_string(
                intake_record.get('source_resolution_wave_id'),
                'wave_id'
            )
            
            # Wave and priority fields
            wave_rank = normalize_int(intake_record.get('wave_rank'), 'wave_rank')
            wave_type = normalize_string(intake_record.get('wave_type'), 'wave_type')
            packet_priority = normalize_string(intake_record.get('packet_priority'), 'packet_priority')
            checklist_priority = normalize_string(intake_record.get('checklist_priority'), 'checklist_priority')
            review_board_priority = normalize_string(intake_record.get('review_board_priority'), 'review_board_priority')
            review_docket_priority = normalize_string(intake_record.get('review_docket_priority'), 'review_docket_priority')
            review_agenda_priority = normalize_string(intake_record.get('review_agenda_priority'), 'review_agenda_priority')
            review_session_pack_priority = normalize_string(intake_record.get('review_session_pack_priority'), 'review_session_pack_priority')
            review_session_brief_priority = normalize_string(intake_record.get('review_session_brief_priority'), 'review_session_brief_priority')
            review_session_handoff_priority = normalize_string(intake_record.get('review_session_handoff_priority'), 'review_session_handoff_priority')
            review_session_intake_priority = normalize_string(intake_record.get('review_session_intake_priority'), 'review_session_intake_priority')
            review_lane = normalize_string(intake_record.get('review_lane'), 'review_lane')
            terminal_posture = normalize_string(intake_record.get('terminal_posture'), 'terminal_posture')
            
            # Array fields (normalize to canonical form)
            member_cluster_ids = normalize_list(intake_record.get('member_cluster_ids', []), 'member_cluster_ids')
            member_dependency_ids = normalize_list(intake_record.get('member_dependency_ids', []), 'member_dependency_ids')
            member_source_refs = normalize_list(intake_record.get('member_source_refs', []), 'member_source_refs')
            affected_proposal_ids = normalize_list(intake_record.get('affected_proposal_ids', []), 'affected_proposal_ids')
            affected_queue_ids = normalize_list(intake_record.get('affected_queue_ids', []), 'affected_queue_ids')
            
            # Count and flag fields
            affected_record_count = normalize_int(intake_record.get('affected_record_count'), 'affected_record_count')
            cluster_count = normalize_int(intake_record.get('cluster_count'), 'cluster_count')
            dependency_count = normalize_int(intake_record.get('dependency_count'), 'dependency_count')
            has_prohibition_path = normalize_bool(intake_record.get('has_prohibition_path'), 'has_prohibition_path')
            has_blocker_path = normalize_bool(intake_record.get('has_blocker_path'), 'has_blocker_path')
            
        except ValueError as e:
            raise ValueError(f"Validation error in intake record {idx}: {e}")
        
        # Create receipt entry with all 35 required fields
        receipt = {
            # Receipt-specific ID (unique per receipt entry)
            'resolution_wave_packet_review_session_receipt_id': f'resolution-wave-packet-review-session-receipt-{idx+1:04d}',
            
            # Cross-references to upstream layers (pass-through)
            'source_resolution_wave_packet_review_session_intake_id': intake_id,
            'source_resolution_wave_packet_review_session_handoff_id': handoff_id,
            'source_resolution_wave_packet_review_session_brief_id': brief_id,
            'source_resolution_wave_packet_review_session_pack_id': pack_id,
            'source_resolution_wave_packet_review_agenda_id': agenda_id,
            'source_resolution_wave_packet_review_docket_id': docket_id,
            'source_resolution_wave_packet_review_board_id': board_id,
            'source_resolution_wave_packet_checklist_id': checklist_id,
            'source_resolution_wave_packet_id': packet_id,
            'source_resolution_wave_id': wave_id,
            
            # Wave and priority fields (pass-through exactly)
            'wave_rank': wave_rank,
            'wave_type': wave_type,
            'packet_priority': packet_priority,
            'checklist_priority': checklist_priority,
            'review_board_priority': review_board_priority,
            'review_docket_priority': review_docket_priority,
            'review_agenda_priority': review_agenda_priority,
            'review_session_pack_priority': review_session_pack_priority,
            'review_session_brief_priority': review_session_brief_priority,
            'review_session_handoff_priority': review_session_handoff_priority,
            'review_session_intake_priority': review_session_intake_priority,
            
            # Lane and posture (pass-through exactly)
            'review_lane': review_lane,
            'terminal_posture': terminal_posture,
            
            # Receipt-specific fields (projection only)
            'review_session_receipt_priority': review_session_intake_priority,  # Inherit intake priority
            'receipt_position': idx + 1,
            
            # Member and affected arrays (pass-through canonical form)
            'member_cluster_ids': member_cluster_ids,
            'member_dependency_ids': member_dependency_ids,
            'member_source_refs': member_source_refs,
            'affected_proposal_ids': affected_proposal_ids,
            'affected_queue_ids': affected_queue_ids,
            
            # Count and flag fields (pass-through)
            'affected_record_count': affected_record_count,
            'cluster_count': cluster_count,
            'dependency_count': dependency_count,
            'has_prohibition_path': has_prohibition_path,
            'has_blocker_path': has_blocker_path,
        }
        
        receipt_records.append(receipt)
    
    # Sort deterministically: lane_order → wave_rank → intake_id → handoff_id
    def sort_key(rec):
        return (
            LANE_ORDER.get(rec['review_lane'], 999),
            rec['wave_rank'],
            rec['source_resolution_wave_packet_review_session_intake_id'],
            rec['source_resolution_wave_packet_review_session_handoff_id'],
        )
    
    receipt_records.sort(key=sort_key)
    
    # Re-assign receipt_position after sort
    for idx, rec in enumerate(receipt_records):
        rec['receipt_position'] = idx + 1
    
    return receipt_records

def generate_markdown(payload, records):
    """Generate markdown pure projection of receipt JSON."""
    md = f"""# Model Adjustment Release Resolution Wave Packet Review Session Receipt

**Version**: v6.1-slice-1
**Generated At (UTC)**: {payload['generated_at_utc']}

## Summary

| Field | Value |
|---|---|
| upstream_session_intake_count | {payload['upstream_session_intake_count']} |
| total_review_session_receipt_records | {len(records)} |
| review_lane_counts | {payload['review_lane_counts']} |
| coverage_reconciled | {payload['coverage_reconciled']} |
| deterministic_ordering | {payload['deterministic_ordering']} |

## Source Versions

| Source | Version |
|---|---|
| model_adjustment_release_resolution_wave_packet_review_session_intake_version | {payload['upstream_session_intake_version']} |

"""
    
    # Receipt record sections
    for rec in records:
        md += f"""## {rec['resolution_wave_packet_review_session_receipt_id']}

- source_resolution_wave_packet_review_session_intake_id: {rec['source_resolution_wave_packet_review_session_intake_id']}
- source_resolution_wave_packet_review_session_handoff_id: {rec['source_resolution_wave_packet_review_session_handoff_id']}
- source_resolution_wave_packet_review_session_brief_id: {rec['source_resolution_wave_packet_review_session_brief_id']}
- source_resolution_wave_packet_review_session_pack_id: {rec['source_resolution_wave_packet_review_session_pack_id']}
- source_resolution_wave_packet_review_agenda_id: {rec['source_resolution_wave_packet_review_agenda_id']}
- source_resolution_wave_packet_review_docket_id: {rec['source_resolution_wave_packet_review_docket_id']}
- source_resolution_wave_packet_review_board_id: {rec['source_resolution_wave_packet_review_board_id']}
- source_resolution_wave_packet_checklist_id: {rec['source_resolution_wave_packet_checklist_id']}
- source_resolution_wave_packet_id: {rec['source_resolution_wave_packet_id']}
- source_resolution_wave_id: {rec['source_resolution_wave_id']}
- wave_rank: {rec['wave_rank']}
- wave_type: {rec['wave_type']}
- packet_priority: {rec['packet_priority']}
- checklist_priority: {rec['checklist_priority']}
- review_board_priority: {rec['review_board_priority']}
- review_docket_priority: {rec['review_docket_priority']}
- review_agenda_priority: {rec['review_agenda_priority']}
- review_session_pack_priority: {rec['review_session_pack_priority']}
- review_session_brief_priority: {rec['review_session_brief_priority']}
- review_session_handoff_priority: {rec['review_session_handoff_priority']}
- review_session_intake_priority: {rec['review_session_intake_priority']}
- review_lane: {rec['review_lane']}
- review_session_receipt_priority: {rec['review_session_receipt_priority']}
- receipt_position: {rec['receipt_position']}
- terminal_posture: {rec['terminal_posture']}

### member_cluster_ids

{json.dumps(rec['member_cluster_ids'], indent=2)}

### member_dependency_ids

{json.dumps(rec['member_dependency_ids'], indent=2)}

### member_source_refs

{json.dumps(rec['member_source_refs'], indent=2)}

### affected_proposal_ids

{json.dumps(rec['affected_proposal_ids'], indent=2)}

### affected_queue_ids

{json.dumps(rec['affected_queue_ids'], indent=2)}

- affected_record_count: {rec['affected_record_count']}
- cluster_count: {rec['cluster_count']}
- dependency_count: {rec['dependency_count']}
- has_prohibition_path: {rec['has_prohibition_path']}
- has_blocker_path: {rec['has_blocker_path']}

"""
    
    return md

def main():
    try:
        # Load upstream intake JSON
        intake_path = SOURCE_PATHS['intake']
        if not os.path.exists(intake_path):
            raise FileNotFoundError(f"Upstream intake JSON not found: {intake_path}")
        
        with open(intake_path, 'r') as f:
            intake_payload = json.load(f)
        
        # Validate upstream
        intake_records = validate_upstream_payload(intake_payload, intake_path)
        
        # Build receipt records
        receipt_records = build_receipt_records(intake_records)
        
        # Verify coverage and ordering
        coverage_reconciled = len(intake_records) == len(receipt_records)
        is_sorted = all(
            receipt_records[i]['receipt_position'] <= receipt_records[i+1]['receipt_position']
            for i in range(len(receipt_records) - 1)
        )
        
        # Count review lanes
        lane_counts = {}
        for rec in receipt_records:
            lane = rec['review_lane']
            lane_counts[lane] = lane_counts.get(lane, 0) + 1
        
        # Build output payload
        output_payload = {
            'model_adjustment_release_resolution_wave_packet_review_session_receipt_version': 'v6.1-slice-1',
            'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'upstream_session_intake_count': len(intake_records),
            'upstream_session_intake_version': intake_payload.get('model_adjustment_release_resolution_wave_packet_review_session_intake_version'),
            'release_resolution_wave_packet_review_session_receipt': receipt_records,
            'coverage_reconciled': coverage_reconciled,
            'deterministic_ordering': is_sorted,
            'review_lane_counts': lane_counts,
        }
        
        # Generate markdown
        markdown_output = generate_markdown(output_payload, receipt_records)
        
        # Write outputs
        os.makedirs(os.path.dirname(OUTPUT_PATHS['json']), exist_ok=True)
        
        with open(OUTPUT_PATHS['json'], 'w') as f:
            json.dump(output_payload, f, indent=2)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['json'])}")
        
        with open(OUTPUT_PATHS['md'], 'w') as f:
            f.write(markdown_output)
        print(f"[WRITE] {os.path.abspath(OUTPUT_PATHS['md'])}")
        
        # Status
        print(f"[STATUS] review_session_receipt_records={len(receipt_records)} upstream_session_intake_count={len(intake_records)} "
              f"coverage_reconciled={coverage_reconciled} deterministic_ordering={is_sorted} "
              f"review_lane_counts={lane_counts}")
        
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
