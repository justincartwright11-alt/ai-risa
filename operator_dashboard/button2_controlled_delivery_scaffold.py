from flask import Blueprint, request, jsonify

controlled_delivery = Blueprint('controlled_delivery', __name__)

@controlled_delivery.route('/api/button2/controlled-delivery/preview', methods=['POST'])
def controlled_delivery_preview():
    data = request.get_json()

    # Validate required fields
    required_fields = [
        'report_id', 'report_status', 'customer_identity', 'delivery_target',
        'delivery_channel', 'operator_approval', 'delivery_evidence',
        'audit_record', 'proof_of_delivery', 'rollback_pointer'
    ]

    missing_fields = [field for field in required_fields if field not in data]
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