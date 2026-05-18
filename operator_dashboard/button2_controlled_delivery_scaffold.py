from flask import Blueprint, request, jsonify
import uuid
import json
from datetime import datetime

controlled_delivery = Blueprint('controlled_delivery', __name__)

@controlled_delivery.route('/api/button2/controlled-delivery/preview', methods=['POST'])
def controlled_delivery_preview():
    data = request.get_json()
    if data is None:
        data = {}

    # Validate that required fields exist (but allow None/False values for some)
    required_field_names = [
        'report_id', 'report_status', 'customer_identity', 'delivery_target',
        'delivery_channel', 'operator_approval', 'delivery_evidence',
        'audit_record', 'proof_of_delivery', 'rollback_pointer'
    ]

    missing_fields = [field for field in required_field_names if field not in data]
    if missing_fields:
        return jsonify({
            'controlled_delivery_preview': False,
            'delivery_ready': False,
            'denial_reason': 'missing_required_fields',
            'denial_reasons': missing_fields,
            'safety_flags': {
                'live_delivery_performed': False,
                'customer_delivery_performed': False,
                'email_send_performed': False,
                'database_write_performed': False,
                'queue_write_performed': False,
                'ledger_write_performed': False,
                'learning_apply_performed': False,
                'calibration_write_performed': False,
                'button1_mutation_performed': False,
                'button3_mutation_performed': False
            }
        }), 400

    # Denial reasons
    denial_reasons = []
    if not data.get('operator_approval'):
        denial_reasons.append('operator_approval_required')
    if data.get('report_status') != 'customer_ready':
        denial_reasons.append('customer_ready_report_required')
    if data.get('report_status') in ['draft', 'internal', 'draft_internal']:
        denial_reasons.append('draft_internal_report_blocked')
    if not data.get('customer_identity'):
        denial_reasons.append('missing_customer_identity')
    if not data.get('delivery_target'):
        denial_reasons.append('missing_delivery_target')
    if not data.get('delivery_evidence'):
        denial_reasons.append('missing_delivery_evidence')
    if not data.get('audit_record'):
        denial_reasons.append('missing_audit_record')
    if not data.get('proof_of_delivery'):
        denial_reasons.append('proof_of_delivery_required')
    if not data.get('rollback_pointer'):
        denial_reasons.append('rollback_pointer_required')

    # If there are denial reasons, return them
    if denial_reasons:
        return jsonify({
            'controlled_delivery_preview': False,
            'delivery_ready': False,
            'denial_reason': denial_reasons[0],
            'denial_reasons': denial_reasons,
            'safety_flags': {
                'live_delivery_performed': False,
                'customer_delivery_performed': False,
                'email_send_performed': False,
                'database_write_performed': False,
                'queue_write_performed': False,
                'ledger_write_performed': False,
                'learning_apply_performed': False,
                'calibration_write_performed': False,
                'button1_mutation_performed': False,
                'button3_mutation_performed': False
            }
        }), 400

    # If all validations pass, return a successful preview response
    return jsonify({
        'controlled_delivery_preview': True,
        'delivery_ready': True,
        'denial_reason': None,
        'denial_reasons': [],
        'report_id': data['report_id'],
        'report_status': data['report_status'],
        'customer_identity_present': bool(data.get('customer_identity')),
        'delivery_target_present': bool(data.get('delivery_target')),
        'delivery_channel': data.get('delivery_channel'),
        'audit_ready': bool(data.get('audit_record')),
        'rollback_ready': bool(data.get('rollback_pointer')),
        'proof_of_delivery_ready': bool(data.get('proof_of_delivery')),
        'operation_id': 'preview-' + data['report_id'],
        'safety_flags': {
            'live_delivery_performed': False,
            'customer_delivery_performed': False,
            'email_send_performed': False,
            'database_write_performed': False,
            'queue_write_performed': False,
            'ledger_write_performed': False,
            'learning_apply_performed': False,
            'calibration_write_performed': False,
            'button1_mutation_performed': False,
            'button3_mutation_performed': False
        }
    }), 200


@controlled_delivery.route('/api/button2/controlled-delivery/action', methods=['POST'])
def controlled_delivery_action():
    """
    Operator-approved controlled delivery action endpoint.
    
    Validates all preconditions:
    1. operator_approval must be true
    2. report_status must be "customer_ready"
    3. customer_identity must be present
    4. delivery_target must be present
    5. delivery_channel must be supported
    6. delivery_evidence must be present
    7. audit_record must be present
    8. proof_of_delivery must be present
    9. rollback_pointer must be present
    10. draft/internal flags must be absent
    
    Only executes delivery if ALL preconditions pass.
    All safety flags remain false except for manual_export delivery when approved.
    """
    data = request.get_json()
    if data is None:
        data = {}

    # Generate operation IDs
    operation_id = str(uuid.uuid4())
    audit_id = str(uuid.uuid4())
    rollback_id = str(uuid.uuid4())
    delivery_receipt_id = str(uuid.uuid4())

    # Validate that required fields exist
    required_field_names = [
        'report_id', 'report_status', 'customer_identity', 'delivery_target',
        'delivery_channel', 'operator_approval', 'delivery_evidence',
        'audit_record', 'proof_of_delivery', 'rollback_pointer'
    ]

    missing_fields = [field for field in required_field_names if field not in data]
    
    # Supported delivery channels for this backend slice
    supported_channels = ['manual_export', 'email_scaffold', 'api_scaffold']

    # Validate all preconditions
    denial_reasons = []
    
    # Check for missing required fields first and map to semantic denial reasons
    if 'operator_approval' not in data:
        denial_reasons.append('operator_approval_required')
    if 'report_status' not in data:
        denial_reasons.append('customer_ready_report_required')
    if 'customer_identity' not in data:
        denial_reasons.append('missing_customer_identity')
    if 'delivery_target' not in data:
        denial_reasons.append('missing_delivery_target')
    if 'delivery_channel' not in data:
        denial_reasons.append('unsupported_delivery_channel')
    if 'delivery_evidence' not in data:
        denial_reasons.append('missing_delivery_evidence')
    if 'audit_record' not in data:
        denial_reasons.append('missing_audit_record')
    if 'proof_of_delivery' not in data:
        denial_reasons.append('proof_of_delivery_required')
    if 'rollback_pointer' not in data:
        denial_reasons.append('rollback_pointer_required')
    
    # If any required fields are missing, return early with denials
    if denial_reasons:
        return jsonify({
            'controlled_delivery_action': False,
            'delivery_action_ready': False,
            'delivery_action_performed': False,
            'denial_reason': denial_reasons[0],
            'denial_reasons': denial_reasons,
            'operation_id': operation_id,
            'report_id': data.get('report_id'),
            'report_status': data.get('report_status'),
            'customer_identity_present': False,
            'delivery_target_present': False,
            'delivery_channel': data.get('delivery_channel'),
            'audit_ready': False,
            'rollback_ready': False,
            'proof_of_delivery_ready': False,
            'safety_flags': {
                'live_delivery_performed': False,
                'customer_delivery_performed': False,
                'email_send_performed': False,
                'external_api_delivery_performed': False,
                'database_write_performed': False,
                'queue_write_performed': False,
                'ledger_write_performed': False,
                'learning_apply_performed': False,
                'calibration_write_performed': False,
                'button1_mutation_performed': False,
                'button3_mutation_performed': False
            }
        }), 400

    # All required fields present, now validate preconditions
    denial_reasons = []
    
    # Precondition 1: operator_approval must be true
    if not data.get('operator_approval'):
        denial_reasons.append('operator_approval_required')
    
    # Precondition 2: report_status must be customer_ready
    if data.get('report_status') != 'customer_ready':
        denial_reasons.append('customer_ready_report_required')
    
    # Precondition 2b: draft/internal blocking
    if data.get('report_status') in ['draft', 'internal', 'draft_internal']:
        if 'draft_internal_report_blocked' not in denial_reasons:
            denial_reasons.append('draft_internal_report_blocked')
    
    # Precondition 2c: draft_flag or internal_flag blocking
    if data.get('draft_flag') or data.get('internal_flag'):
        if 'draft_internal_report_blocked' not in denial_reasons:
            denial_reasons.append('draft_internal_report_blocked')
    
    # Precondition 3: customer_identity must be present and non-empty
    if not data.get('customer_identity'):
        denial_reasons.append('missing_customer_identity')
    
    # Precondition 4: delivery_target must be present and non-empty
    if not data.get('delivery_target'):
        denial_reasons.append('missing_delivery_target')
    
    # Precondition 5: delivery_channel must be supported
    if data.get('delivery_channel') not in supported_channels:
        denial_reasons.append('unsupported_delivery_channel')
    
    # Precondition 6: delivery_evidence must be present and non-empty
    if not data.get('delivery_evidence'):
        denial_reasons.append('missing_delivery_evidence')
    
    # Precondition 7: audit_record must be present and non-empty
    if not data.get('audit_record'):
        denial_reasons.append('missing_audit_record')
    
    # Precondition 8: proof_of_delivery must be present and non-empty
    if not data.get('proof_of_delivery'):
        denial_reasons.append('proof_of_delivery_required')
    
    # Precondition 9: rollback_pointer must be present and non-empty
    if not data.get('rollback_pointer'):
        denial_reasons.append('rollback_pointer_required')

    # If there are denial reasons, return denial response
    if denial_reasons:
        return jsonify({
            'controlled_delivery_action': False,
            'delivery_action_ready': False,
            'delivery_action_performed': False,
            'denial_reason': denial_reasons[0],
            'denial_reasons': denial_reasons,
            'report_id': data.get('report_id'),
            'report_status': data.get('report_status'),
            'customer_identity_present': bool(data.get('customer_identity')),
            'delivery_target_present': bool(data.get('delivery_target')),
            'delivery_channel': data.get('delivery_channel'),
            'audit_ready': bool(data.get('audit_record')),
            'rollback_ready': bool(data.get('rollback_pointer')),
            'proof_of_delivery_ready': bool(data.get('proof_of_delivery')),
            'operation_id': operation_id,
            'safety_flags': {
                'live_delivery_performed': False,
                'customer_delivery_performed': False,
                'email_send_performed': False,
                'external_api_delivery_performed': False,
                'database_write_performed': False,
                'queue_write_performed': False,
                'ledger_write_performed': False,
                'learning_apply_performed': False,
                'calibration_write_performed': False,
                'button1_mutation_performed': False,
                'button3_mutation_performed': False
            }
        }), 400

    # All preconditions passed - delivery action is ready
    
    # Determine delivery mode and whether delivery was actually performed
    delivery_channel = data.get('delivery_channel')
    delivery_action_performed = False
    live_delivery_performed = False
    customer_delivery_performed = False
    email_send_performed = False
    external_api_delivery_performed = False

    # For this backend slice:
    # - manual_export: Mark as performed only if operator approved
    # - email_scaffold: Scaffold only (not actually sent)
    # - api_scaffold: Scaffold only (not actually called)
    
    if delivery_channel == 'manual_export':
        # Manual export can be marked as delivered if all preconditions pass
        delivery_action_performed = True
        live_delivery_performed = True
        customer_delivery_performed = True
    elif delivery_channel == 'email_scaffold':
        # Email is scaffolded but not actually sent in this slice
        delivery_action_performed = False
        email_send_performed = False
    elif delivery_channel == 'api_scaffold':
        # API is scaffolded but not actually called in this slice
        delivery_action_performed = False
        external_api_delivery_performed = False

    # Create audit trail
    audit_record = {
        'audit_id': audit_id,
        'audit_timestamp': datetime.utcnow().isoformat(),
        'operation_id': operation_id,
        'report_id': data.get('report_id'),
        'customer_identity': data.get('customer_identity'),
        'delivery_target': data.get('delivery_target'),
        'delivery_channel': delivery_channel,
        'delivery_evidence': data.get('delivery_evidence'),
        'delivery_action_performed': delivery_action_performed,
        'all_preconditions_passed': True
    }

    # Return successful action response
    return jsonify({
        'controlled_delivery_action': True,
        'delivery_action_ready': True,
        'delivery_action_performed': delivery_action_performed,
        'denial_reason': None,
        'denial_reasons': [],
        'report_id': data.get('report_id'),
        'report_status': data.get('report_status'),
        'customer_identity_present': bool(data.get('customer_identity')),
        'delivery_target_present': bool(data.get('delivery_target')),
        'delivery_channel': delivery_channel,
        'audit_ready': bool(data.get('audit_record')),
        'rollback_ready': bool(data.get('rollback_pointer')),
        'proof_of_delivery_ready': bool(data.get('proof_of_delivery')),
        'operation_id': operation_id,
        'audit_id': audit_id,
        'rollback_id': rollback_id,
        'delivery_receipt_id': delivery_receipt_id,
        'delivery_mode': delivery_channel,
        'audit_record': audit_record,
        'safety_flags': {
            'live_delivery_performed': live_delivery_performed,
            'customer_delivery_performed': customer_delivery_performed,
            'email_send_performed': email_send_performed,
            'external_api_delivery_performed': external_api_delivery_performed,
            'database_write_performed': False,
            'queue_write_performed': False,
            'ledger_write_performed': False,
            'learning_apply_performed': False,
            'calibration_write_performed': False,
            'button1_mutation_performed': False,
            'button3_mutation_performed': False
        }
    }), 200