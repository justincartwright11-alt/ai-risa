import unittest
import json
import os
import tempfile
import hashlib
import uuid
from pathlib import Path
from unittest.mock import patch
from time import time
from datetime import datetime, timezone
import app as app_module
from app import (
    app,
    _build_approved_apply_report_scoring_bridge_evidence,
    _build_structural_signal_backfill_planner,
    _build_batch_preview_execution_token,
    _build_selected_keys_digest,
    _is_allowed_official_source_url,
    _classify_official_source_host,
    _build_citation_fingerprint,
    _classify_source_confidence,
    _validate_official_source_citation,
)
from operator_dashboard.official_source_approved_apply_global_ledger_helper import OfficialSourceApprovedApplyGlobalLedgerHelper
from official_source_approved_apply_token import issue_official_source_approved_apply_token
from operator_dashboard.official_source_approved_apply_operation_id_persistence_helper import OfficialSourceApprovedApplyOperationIdPersistenceHelper
from official_source_acceptance_gate import evaluate_official_source_acceptance_gate
from official_source_approved_apply_token_consume_helper import OfficialSourceApprovedApplyTokenConsumeHelper
from operator_dashboard.official_source_lookup_provider import OfficialSourceLookupProvider

class DashboardBackendTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self._original_mutation_enabled = app.config.get('OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED')
        self._original_accuracy_override = app.config.get('OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE')
        self._original_operation_id_audit_override = app.config.get('OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE')
        self._original_global_ledger_override = app.config.get('OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE')
        self._original_consume_helper = app_module.OFFICIAL_SOURCE_APPROVED_APPLY_TOKEN_CONSUME_HELPER
        self._original_global_ledger_helper = app_module.OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_HELPER
        self._original_operation_id_persistence_helper = app_module.OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_PERSISTENCE_HELPER

        app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = False
        app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = None
        app.config['OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE'] = None
        app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = None
        app_module.OFFICIAL_SOURCE_APPROVED_APPLY_TOKEN_CONSUME_HELPER = OfficialSourceApprovedApplyTokenConsumeHelper()
        app_module.OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_HELPER = OfficialSourceApprovedApplyGlobalLedgerHelper()
        app_module.OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_PERSISTENCE_HELPER = OfficialSourceApprovedApplyOperationIdPersistenceHelper()

    def tearDown(self):
        app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = self._original_mutation_enabled
        app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = self._original_accuracy_override
        app.config['OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE'] = self._original_operation_id_audit_override
        app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = self._original_global_ledger_override
        app_module.OFFICIAL_SOURCE_APPROVED_APPLY_TOKEN_CONSUME_HELPER = self._original_consume_helper
        app_module.OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_HELPER = self._original_global_ledger_helper
        app_module.OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_PERSISTENCE_HELPER = self._original_operation_id_persistence_helper

    def _official_preview_payload(self, selected_key='alpha_vs_beta|predictions_alpha_vs_beta_prediction_json', **overrides):
        payload = {
            'selected_key': selected_key,
            'mode': 'official_source_one_record',
            'lookup_intent': 'preview_only',
            'approval_granted': False,
        }
        payload.update(overrides)
        return payload

    def _official_approved_apply_payload(self, selected_key='alpha_vs_beta|predictions_alpha_vs_beta_prediction_json', **overrides):
        source_date = datetime.now(timezone.utc).date().isoformat()
        payload = {
            'mode': 'official_source_approved_apply',
            'lookup_intent': 'apply_write',
            'selected_key': selected_key,
            'approval_granted': True,
            'approval_binding': {
                'selected_key': selected_key,
                'citation_fingerprint': 'fp_alpha_beta_123',
                'source_url': 'https://ufc.com/event/test-card',
                'source_date': source_date,
                'extracted_winner': 'Alpha',
                'record_fight_id': 'alpha_vs_beta',
                'selected_row_identity': {
                    'fight_name': 'Alpha vs Beta',
                    'fight_id': 'alpha_vs_beta',
                },
            },
            'preview_snapshot': {
                'selected_key': selected_key,
                'reason_code': 'accepted_preview_write_eligible',
                'manual_review_required': False,
                'source_citation': {
                    'source_url': 'https://ufc.com/event/test-card',
                    'source_title': 'UFC Test Card',
                    'source_date': source_date,
                    'publisher_host': 'ufc.com',
                    'source_confidence': 'tier_a0',
                    'confidence_score': 0.85,
                    'citation_fingerprint': 'fp_alpha_beta_123',
                    'extracted_winner': 'Alpha',
                    'method': 'Decision',
                    'round_time': 'R3 5:00',
                },
                'acceptance_gate': {
                    'state': 'write_eligible',
                    'write_eligible': True,
                    'reason_code': 'accepted_preview_write_eligible',
                    'selected_key': selected_key,
                    'citation_fingerprint': 'fp_alpha_beta_123',
                },
                'audit': {
                    'record_fight_id': 'alpha_vs_beta',
                    'fight_name': 'Alpha vs Beta',
                    'provider_attempted': True,
                    'attempted_sources': [],
                },
            },
            'operator_note': 'endpoint skeleton test',
        }
        payload.update(overrides)
        return payload

    def _issue_approved_apply_token(self, payload):
        result = issue_official_source_approved_apply_token(payload['approval_binding'], now_epoch=int(time()), ttl_seconds=300)
        self.assertTrue(result.get('ok'))
        return result.get('token')

    def _assert_approved_apply_normalized_envelope(self, data):
        required_fields = [
            'ok',
            'mode',
            'phase',
            'request_valid',
            'token_valid',
            'guard_allowed',
            'manual_review_required',
            'approval_required',
            'approval_granted',
            'approval_binding_valid',
            'token_status',
            'approval_token_status',
            'mutation_performed',
            'write_performed',
            'bulk_lookup_performed',
            'scoring_semantics_changed',
            'external_lookup_performed',
            'reason_code',
            'errors',
            'selected_key',
            'acceptance_gate',
            'binding_digest_expected',
            'binding_digest_actual',
            'token_id',
            'fight_id',
            'proposed_write',
            'write_target',
            'before_row_count',
            'after_row_count',
            'pre_write_file_sha256',
            'post_write_file_sha256',
            'rollback_attempted',
            'rollback_succeeded',
            'post_rollback_file_sha256',
            'rollback_reason_code',
            'rollback_error_detail',
            'rollback_started_at_utc',
            'rollback_finished_at_utc',
            'rollback_terminal_state',
            'escalation_required',
            'operator_escalation_action',
            'approval_token_id',
            'operation_id',
            'write_attempt_id',
            'contract_version',
            'endpoint_version',
            'mutation_enabled',
            'token_consume_performed',
            'token_consume_reason_code',
            'token_consume_idempotent',
            'token_consume_attempted_at_utc',
            'token_consume_completed_at_utc',
            'token_consume_retry_count',
            'message',
        ]
        for field in required_fields:
            self.assertIn(field, data)
        self.assertEqual(data.get('mode'), 'official_source_approved_apply')
        self.assertEqual(data.get('phase'), 'approved_apply')
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertFalse(data.get('scoring_semantics_changed'))
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertEqual(data.get('token_status'), data.get('approval_token_status'))

    def _sha256_or_none(self, path: Path):
        if not path.exists():
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _actual_results_file_hashes(self):
        root = Path(__file__).resolve().parent.parent
        accuracy_dir = root / 'ops' / 'accuracy'
        targets = [
            accuracy_dir / 'actual_results.json',
            accuracy_dir / 'actual_results_manual.json',
            accuracy_dir / 'actual_results_unresolved.json',
        ]
        return {str(p): self._sha256_or_none(p) for p in targets}

    def _read_operation_id_audit_rows(self, audit_path: Path):
        if not audit_path.exists():
            return []
        return app_module.OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_PERSISTENCE_HELPER.read_records(str(audit_path))

    def _read_global_ledger_rows(self, ledger_path: Path):
        if not ledger_path.exists():
            return []
        return app_module.OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_HELPER.read_records(str(ledger_path))

    def _assert_bridge_evidence_fields(self, data):
        required_fields = {
            'prediction_report_id',
            'local_result_key',
            'global_ledger_record_id',
            'official_source_reference',
            'approved_actual_result',
            'predicted_winner_id',
            'predicted_method',
            'predicted_round',
            'confidence',
            'resolved_result_status',
            'scored',
            'score_outcome',
            'calibration_notes',
        }
        self.assertEqual(set(data.keys()), required_fields)

    def _acceptance_gate_preview_result(self, **overrides):
        base = {
            'ok': True,
            'mode': 'official_source_one_record',
            'phase': 'lookup_preview',
            'selected_key': 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json',
            'approval_required': True,
            'approval_granted': False,
            'mutation_performed': False,
            'external_lookup_performed': True,
            'bulk_lookup_performed': False,
            'scoring_semantics_changed': False,
            'manual_review_required': False,
            'reason_code': 'accepted_preview',
            'source_citation': {
                'source_url': 'https://ufc.com/event/test-card',
                'source_title': 'UFC Test Card',
                'source_date': datetime.now(timezone.utc).date().isoformat(),
                'publisher_host': 'ufc.com',
                'source_confidence': 'tier_a0',
                'confidence_score': 0.85,
                'citation_fingerprint': 'abc123fingerprint',
                'extracted_winner': 'Alpha',
                'identity_matches_selected_row': True,
            },
        }
        base.update(overrides)
        return base

    def test_report_scoring_bridge_clean_scored_report(self):
        prediction_report = {
            'prediction_report_id': 'report_alpha_1',
            'local_result_key': 'alpha_vs_beta',
            'predicted_winner_id': 'Alpha',
            'predicted_method': 'Decision',
            'predicted_round': 'R3',
            'confidence': 0.82,
        }
        approved_actual_rows = [{
            'fight_id': 'alpha_vs_beta',
            'actual_winner': 'Alpha',
            'actual_method': 'Decision',
            'actual_round': 'R3',
        }]
        global_ledger_rows = [{
            'global_ledger_record_id': 'glr_1',
            'local_result_key': 'alpha_vs_beta',
            'official_source_reference': {'source_url': 'https://ufc.com/event/test-card'},
            'approved_actual_result': {
                'fight_id': 'alpha_vs_beta',
                'actual_winner': 'Alpha',
                'actual_method': 'Decision',
                'actual_round': 'R3',
            },
        }]

        data = _build_approved_apply_report_scoring_bridge_evidence(
            prediction_report,
            approved_actual_rows,
            global_ledger_rows,
        )
        self._assert_bridge_evidence_fields(data)
        self.assertTrue(data.get('scored'))
        self.assertEqual(data.get('resolved_result_status'), 'resolved')
        self.assertEqual(data.get('score_outcome'), 'round_exact')
        self.assertEqual(data.get('global_ledger_record_id'), 'glr_1')

    def test_report_scoring_bridge_unresolved_when_no_approved_actual(self):
        prediction_report = {
            'prediction_report_id': 'report_alpha_2',
            'local_result_key': 'alpha_vs_beta',
            'predicted_winner_id': 'Alpha',
            'predicted_method': 'Decision',
            'predicted_round': 'R3',
            'confidence': 0.71,
        }

        data = _build_approved_apply_report_scoring_bridge_evidence(
            prediction_report,
            approved_actual_rows=[],
            global_ledger_rows=[],
        )
        self._assert_bridge_evidence_fields(data)
        self.assertFalse(data.get('scored'))
        self.assertEqual(data.get('resolved_result_status'), 'no_actual_found')
        self.assertEqual(data.get('score_outcome'), 'unresolved')

    def test_report_scoring_bridge_mismatch_is_deterministic(self):
        prediction_report = {
            'prediction_report_id': 'report_alpha_3',
            'local_result_key': 'alpha_vs_beta',
            'predicted_winner_id': 'Alpha',
            'predicted_method': 'KO',
            'predicted_round': 'R1',
            'confidence': 0.64,
        }
        approved_actual_rows = [{
            'fight_id': 'alpha_vs_beta',
            'actual_winner': 'Beta',
            'actual_method': 'Decision',
            'actual_round': 'R3',
        }]
        global_ledger_rows = [{
            'global_ledger_record_id': 'glr_2',
            'local_result_key': 'alpha_vs_beta',
            'official_source_reference': {'source_url': 'https://ufc.com/event/test-card'},
            'approved_actual_result': {
                'fight_id': 'alpha_vs_beta',
                'actual_winner': 'Beta',
                'actual_method': 'Decision',
                'actual_round': 'R3',
            },
        }]

        data = _build_approved_apply_report_scoring_bridge_evidence(
            prediction_report,
            approved_actual_rows,
            global_ledger_rows,
        )
        self._assert_bridge_evidence_fields(data)
        self.assertTrue(data.get('scored'))
        self.assertEqual(data.get('resolved_result_status'), 'resolved')
        self.assertEqual(data.get('score_outcome'), 'mismatch')

    def test_report_scoring_bridge_duplicate_conflict_from_duplicate_ledger_trace(self):
        prediction_report = {
            'prediction_report_id': 'report_alpha_4',
            'local_result_key': 'alpha_vs_beta',
            'predicted_winner_id': 'Alpha',
            'predicted_method': 'Decision',
            'predicted_round': 'R3',
            'confidence': 0.88,
        }
        approved_actual_rows = [{
            'fight_id': 'alpha_vs_beta',
            'actual_winner': 'Alpha',
            'actual_method': 'Decision',
            'actual_round': 'R3',
        }]
        global_ledger_rows = [
            {
                'global_ledger_record_id': 'glr_3a',
                'local_result_key': 'alpha_vs_beta',
                'official_source_reference': {'source_url': 'https://ufc.com/event/test-card'},
                'approved_actual_result': {'fight_id': 'alpha_vs_beta', 'actual_winner': 'Alpha'},
            },
            {
                'global_ledger_record_id': 'glr_3b',
                'local_result_key': 'alpha_vs_beta',
                'official_source_reference': {'source_url': 'https://ufc.com/event/test-card'},
                'approved_actual_result': {'fight_id': 'alpha_vs_beta', 'actual_winner': 'Alpha'},
            },
        ]

        data = _build_approved_apply_report_scoring_bridge_evidence(
            prediction_report,
            approved_actual_rows,
            global_ledger_rows,
        )
        self._assert_bridge_evidence_fields(data)
        self.assertFalse(data.get('scored'))
        self.assertEqual(data.get('resolved_result_status'), 'duplicate_conflict')
        self.assertEqual(data.get('score_outcome'), 'duplicate_conflict')

    def test_report_scoring_bridge_no_approved_actual_remains_auditable_and_non_mutating(self):
        prediction_report = {
            'prediction_report_id': 'report_alpha_5',
            'local_result_key': 'alpha_vs_beta',
            'predicted_winner_id': 'Alpha',
            'predicted_method': 'Decision',
            'predicted_round': 'R3',
            'confidence': 0.5,
        }
        approved_actual_rows = []
        global_ledger_rows = []

        snapshot_prediction = json.loads(json.dumps(prediction_report))
        snapshot_actual_rows = json.loads(json.dumps(approved_actual_rows))
        snapshot_ledger_rows = json.loads(json.dumps(global_ledger_rows))

        data = _build_approved_apply_report_scoring_bridge_evidence(
            prediction_report,
            approved_actual_rows,
            global_ledger_rows,
        )

        self._assert_bridge_evidence_fields(data)
        self.assertFalse(data.get('scored'))
        self.assertEqual(data.get('resolved_result_status'), 'no_actual_found')
        self.assertIn('no approved actual', str(data.get('calibration_notes') or '').lower())
        self.assertEqual(prediction_report, snapshot_prediction)
        self.assertEqual(approved_actual_rows, snapshot_actual_rows)
        self.assertEqual(global_ledger_rows, snapshot_ledger_rows)

    def test_acceptance_gate_tier_a0_happy_path_write_eligible(self):
        result = evaluate_official_source_acceptance_gate(self._acceptance_gate_preview_result())
        self.assertEqual(result.get('state'), 'write_eligible')
        self.assertTrue(result.get('write_eligible'))
        self.assertEqual(result.get('reason_code'), 'accepted_preview_write_eligible')

    def test_acceptance_gate_tier_a1_happy_path_write_eligible(self):
        payload = self._acceptance_gate_preview_result(source_citation={
            **self._acceptance_gate_preview_result()['source_citation'],
            'source_confidence': 'tier_a1',
            'confidence_score': 0.72,
        })
        result = evaluate_official_source_acceptance_gate(payload)
        self.assertEqual(result.get('state'), 'write_eligible')
        self.assertEqual(result.get('reason_code'), 'accepted_preview_write_eligible')

    def test_acceptance_gate_tier_b_manual_review(self):
        payload = self._acceptance_gate_preview_result(source_citation={
            **self._acceptance_gate_preview_result()['source_citation'],
            'source_confidence': 'tier_b',
            'confidence_score': 0.55,
        })
        result = evaluate_official_source_acceptance_gate(payload)
        self.assertEqual(result.get('state'), 'manual_review')
        self.assertEqual(result.get('reason_code'), 'tier_b_without_corroboration')

    def test_acceptance_gate_stale_source_manual_review(self):
        payload = self._acceptance_gate_preview_result(reason_code='stale_source_date')
        result = evaluate_official_source_acceptance_gate(payload)
        self.assertEqual(result.get('state'), 'manual_review')
        self.assertEqual(result.get('reason_code'), 'stale_source_date')

    def test_acceptance_gate_source_conflict_manual_review(self):
        payload = self._acceptance_gate_preview_result(reason_code='source_conflict')
        result = evaluate_official_source_acceptance_gate(payload)
        self.assertEqual(result.get('state'), 'manual_review')
        self.assertEqual(result.get('reason_code'), 'source_conflict')

    def test_acceptance_gate_confidence_below_threshold_manual_review(self):
        payload = self._acceptance_gate_preview_result(source_citation={
            **self._acceptance_gate_preview_result()['source_citation'],
            'confidence_score': 0.69,
        })
        result = evaluate_official_source_acceptance_gate(payload)
        self.assertEqual(result.get('state'), 'manual_review')
        self.assertEqual(result.get('reason_code'), 'confidence_below_threshold')

    def test_acceptance_gate_identity_conflict_rejected(self):
        payload = self._acceptance_gate_preview_result(reason_code='identity_conflict')
        result = evaluate_official_source_acceptance_gate(payload)
        self.assertEqual(result.get('state'), 'rejected')
        self.assertEqual(result.get('reason_code'), 'identity_conflict')

    def test_acceptance_gate_publisher_host_mismatch_rejected(self):
        payload = self._acceptance_gate_preview_result(reason_code='publisher_host_mismatch')
        result = evaluate_official_source_acceptance_gate(payload)
        self.assertEqual(result.get('state'), 'rejected')
        self.assertEqual(result.get('reason_code'), 'publisher_host_mismatch')

    def test_acceptance_gate_incomplete_citation_rejected(self):
        payload = self._acceptance_gate_preview_result(source_citation={
            **self._acceptance_gate_preview_result()['source_citation'],
            'source_title': '',
        })
        result = evaluate_official_source_acceptance_gate(payload)
        self.assertEqual(result.get('state'), 'rejected')
        self.assertEqual(result.get('reason_code'), 'citation_incomplete')

    def test_acceptance_gate_missing_fingerprint_rejected(self):
        payload = self._acceptance_gate_preview_result(source_citation={
            **self._acceptance_gate_preview_result()['source_citation'],
            'citation_fingerprint': '',
        })
        result = evaluate_official_source_acceptance_gate(payload)
        self.assertEqual(result.get('state'), 'rejected')
        self.assertEqual(result.get('reason_code'), 'missing_citation_fingerprint')

    def test_acceptance_gate_preview_boundary_violation_rejected(self):
        payload = self._acceptance_gate_preview_result(mutation_performed=True)
        result = evaluate_official_source_acceptance_gate(payload)
        self.assertEqual(result.get('state'), 'rejected')
        self.assertEqual(result.get('reason_code'), 'preview_only_boundary_violation')

    @patch('urllib.request.urlopen')
    @patch('operator_dashboard.official_source_lookup_provider.OfficialSourceLookupProvider.run_preview_lookup')
    @patch('app._upsert_single_manual_actual_result')
    def test_acceptance_gate_read_only_no_provider_network_or_upsert_calls(self, mock_upsert, mock_provider_lookup, mock_urlopen):
        mock_upsert.side_effect = AssertionError('upsert should not be called by evaluator')
        mock_provider_lookup.side_effect = AssertionError('provider lookup should not be called by evaluator')
        mock_urlopen.side_effect = AssertionError('network should not be called by evaluator')

        result = evaluate_official_source_acceptance_gate(self._acceptance_gate_preview_result())
        self.assertEqual(result.get('state'), 'write_eligible')
        mock_upsert.assert_not_called()
        mock_provider_lookup.assert_not_called()
        mock_urlopen.assert_not_called()

    def test_acceptance_gate_does_not_mutate_actual_results_files(self):
        before_hashes = self._actual_results_file_hashes()
        _ = evaluate_official_source_acceptance_gate(self._acceptance_gate_preview_result())
        _ = evaluate_official_source_acceptance_gate(self._acceptance_gate_preview_result(reason_code='source_conflict'))
        _ = evaluate_official_source_acceptance_gate(self._acceptance_gate_preview_result(reason_code='identity_conflict'))
        after_hashes = self._actual_results_file_hashes()
        self.assertEqual(before_hashes, after_hashes)

    def test_index(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'AI-RISA Local Operator Dashboard', resp.data)

    def test_run_local_ai_invalid(self):
        resp = self.client.post('/run_local_ai', json={'request_type': 'invalid'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'Invalid request type', resp.data)

    def test_open_file_invalid(self):
        resp = self.client.get('/open_file?file=not_a_file')
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b'Invalid file type', resp.data)

    def test_accuracy_comparison_summary_contract(self):
        resp = self.client.get('/api/accuracy/comparison-summary')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('compared_results', data)
        self.assertIn('waiting_for_results', data)
        self.assertIn('summary_metrics', data)
        self.assertIsInstance(data.get('compared_results'), list)
        self.assertIsInstance(data.get('waiting_for_results'), list)
        self.assertIsInstance(data.get('summary_metrics'), dict)

    def test_operator_waiting_queue_panel_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Waiting For Real Results', resp.data)
        self.assertIn(b'/api/accuracy/comparison-summary', resp.data)

    def test_index_command_center_uses_intent_endpoint(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/operator/intent', resp.data)
        self.assertNotIn(b'/api/operator/mode', resp.data)

    def test_index_compare_handler_targets_compare_endpoint(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'operator-compare-btn', resp.data)
        self.assertIn(b"operatorCompareBtn.addEventListener('click'", resp.data)
        self.assertIn(b'/api/operator/compare-with-result', resp.data)

    def test_compare_endpoint_not_called_on_page_load(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')

        # Compare endpoint must stay behind explicit operator action.
        self.assertIn("operatorCompareBtn.addEventListener('click'", page)
        self.assertIn("/api/operator/compare-with-result", page)

        dom_ready_start = page.find("window.addEventListener('DOMContentLoaded', () => {")
        self.assertNotEqual(dom_ready_start, -1)
        dom_ready_slice = page[dom_ready_start:dom_ready_start + 500]
        self.assertNotIn('/api/operator/compare-with-result', dom_ready_slice)
        self.assertNotIn('/api/operator/web-trigger-scout', dom_ready_slice)

    def test_index_no_automatic_queue_wide_lookup_copy_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Bulk lookup for waiting records does not run automatically.', resp.data)

    def test_index_has_button2_main_dashboard_pdf_controls(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Generate Premium PDF Reports', resp.data)
        self.assertIn(b'main-prf-refresh-queue-btn', resp.data)
        self.assertIn(b'main-prf-select-all', resp.data)
        self.assertIn(b'main-prf-generate-approval', resp.data)
        self.assertIn(b'main-prf-generate-btn', resp.data)
        self.assertIn(b'/api/premium-report-factory/queue', resp.data)
        self.assertIn(b'/api/premium-report-factory/reports/generate', resp.data)
        self.assertIn(b'No result lookup, no learning, no billing, no web discovery.', resp.data)

    def test_index_has_button1_main_dashboard_queue_builder_controls(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Find and Build Fight Queue', resp.data)
        self.assertIn(b'main-prf-run-discovery-btn', resp.data)
        self.assertIn(b'main-prf-parse-preview-btn', resp.data)
        self.assertIn(b'main-prf-intake-select-all', resp.data)
        self.assertIn(b'main-prf-intake-approval', resp.data)
        self.assertIn(b'main-prf-save-selected-btn', resp.data)
        self.assertIn(b'/api/phase1/scan-upcoming-events', resp.data)
        self.assertIn(b'/api/premium-report-factory/intake/preview', resp.data)
        self.assertIn(b'/api/premium-report-factory/queue/save-selected', resp.data)
        self.assertIn(b'Search and analysis are automatic. Permanent writes are blocked until explicit operator approval.', resp.data)

    def test_index_button1_preview_and_save_not_called_on_page_load(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')

        self.assertIn('/api/premium-report-factory/intake/preview', page)
        self.assertIn('/api/premium-report-factory/queue/save-selected', page)
        dom_ready_start = page.find("window.addEventListener('DOMContentLoaded', () => {")
        self.assertNotEqual(dom_ready_start, -1)
        dom_ready_slice = page[dom_ready_start:dom_ready_start + 800]

        # Button 1 preview/save remain behind explicit operator action.
        self.assertNotIn('/api/premium-report-factory/intake/preview', dom_ready_slice)
        self.assertNotIn('/api/premium-report-factory/queue/save-selected', dom_ready_slice)

    def test_index_button2_generate_not_called_on_page_load(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')

        self.assertIn('/api/premium-report-factory/reports/generate', page)
        dom_ready_start = page.find("window.addEventListener('DOMContentLoaded', () => {")
        self.assertNotEqual(dom_ready_start, -1)
        dom_ready_slice = page[dom_ready_start:dom_ready_start + 600]

        # Main dashboard may pre-load queue state, but generation must stay behind explicit click.
        self.assertNotIn('/api/premium-report-factory/reports/generate', dom_ready_slice)

    def test_index_has_button3_result_comparison_learning_controls(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Find Results &amp; Improve Accuracy', resp.data)
        self.assertIn(b'button3-load-waiting-btn', resp.data)
        self.assertIn(b'button3-official-preview-btn', resp.data)
        self.assertIn(b'button3-add-manual-candidate-btn', resp.data)
        self.assertIn(b'button3-apply-approval', resp.data)
        self.assertIn(b'button3-apply-selected-btn', resp.data)
        self.assertIn(b'/api/operator/actual-result-lookup/dry-run-preview', resp.data)
        self.assertIn(b'/api/operator/actual-result-lookup/official-source-one-record-preview', resp.data)
        self.assertIn(b'/api/operator/actual-result-lookup/guarded-single', resp.data)
        self.assertIn(b'/api/operator/actual-result-lookup/manual-single-apply', resp.data)

    def test_index_button3_apply_endpoints_not_called_on_page_load(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')

        self.assertIn('/api/operator/actual-result-lookup/guarded-single', page)
        self.assertIn('/api/operator/actual-result-lookup/manual-single-apply', page)

        dom_ready_start = page.find("window.addEventListener('DOMContentLoaded', () => {")
        self.assertNotEqual(dom_ready_start, -1)
        dom_ready_slice = page[dom_ready_start:dom_ready_start + 1200]

        # Button 3 apply endpoints must remain behind explicit operator action.
        self.assertNotIn('/api/operator/actual-result-lookup/guarded-single', dom_ready_slice)
        self.assertNotIn('/api/operator/actual-result-lookup/manual-single-apply', dom_ready_slice)

    def test_button3_manual_single_apply_requires_approval(self):
        payload = {
            'selected_key': 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json',
            'approval_granted': False,
            'manual_result': {
                'actual_winner': 'Alpha',
                'actual_method': 'Decision',
                'actual_round': 'R3',
            },
        }
        resp = self.client.post('/api/operator/actual-result-lookup/manual-single-apply', json=payload)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('ok'))
        self.assertEqual(data.get('mode'), 'manual_single_apply')
        self.assertTrue(data.get('approval_required'))
        self.assertFalse(data.get('approval_granted'))
        self.assertFalse(data.get('mutation_performed'))
        self.assertIn('approval_granted must be true for manual apply', data.get('error', ''))

    def test_advanced_dashboard_has_interactive_summary_chips(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'summary-chip-health', resp.data)
        self.assertIn(b'summary-chip-accuracy', resp.data)
        self.assertIn(b'summary-chip-backfill', resp.data)
        self.assertIn(b'summary-chip-queue', resp.data)

    def test_advanced_summary_chip_click_wiring_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"chipHealth && chipHealth.addEventListener('click'", resp.data)
        self.assertIn(b"chipAccuracy && chipAccuracy.addEventListener('click'", resp.data)
        self.assertIn(b"chipBackfill && chipBackfill.addEventListener('click'", resp.data)
        self.assertIn(b"chipQueue && chipQueue.addEventListener('click'", resp.data)
        self.assertIn(b'_focusDashboardNode(', resp.data)

    def test_dry_run_preview_endpoint_contract(self):
        resp = self.client.get('/api/operator/actual-result-lookup/dry-run-preview')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('mode'), 'dry_run_preview')
        self.assertIn('waiting_count', data)
        self.assertIn('preview_limit', data)
        self.assertIn('preview_rows', data)
        self.assertIn('required_fields', data)
        self.assertIn('missing_by_row', data)
        self.assertIs(data.get('mutation_performed'), False)
        self.assertIs(data.get('external_lookup_performed'), False)
        self.assertIs(data.get('bulk_lookup_performed'), False)
        self.assertLessEqual(len(data.get('preview_rows') or []), 10)

    def test_dry_run_preview_limit_capped(self):
        resp = self.client.get('/api/operator/actual-result-lookup/dry-run-preview?limit=999')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('preview_limit'), 10)
        self.assertLessEqual(len(data.get('preview_rows') or []), 10)

    def test_dry_run_preview_does_not_mutate_actual_results_files(self):
        root = Path(__file__).resolve().parent.parent
        accuracy_dir = root / 'ops' / 'accuracy'
        targets = [
            accuracy_dir / 'actual_results.json',
            accuracy_dir / 'actual_results_manual.json',
            accuracy_dir / 'actual_results_unresolved.json',
        ]
        before = {str(p): self._sha256_or_none(p) for p in targets}

        resp = self.client.get('/api/operator/actual-result-lookup/dry-run-preview')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIs(data.get('mutation_performed'), False)

        after = {str(p): self._sha256_or_none(p) for p in targets}
        self.assertEqual(before, after)

    def test_advanced_dashboard_has_dry_run_preview_controls(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'operator-dry-run-preview-btn', resp.data)
        self.assertIn(b'operator-dry-run-preview-output', resp.data)
        self.assertIn(b'/api/operator/actual-result-lookup/dry-run-preview', resp.data)
        self.assertIn(b'No web lookup or result write is performed by this preview.', resp.data)

    def test_advanced_dry_run_preview_not_called_on_page_load(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')

        dom_ready_start = page.find("window.addEventListener('DOMContentLoaded', () => {")
        self.assertNotEqual(dom_ready_start, -1)
        dom_ready_slice = page[dom_ready_start:dom_ready_start + 900]
        self.assertNotIn('/api/operator/actual-result-lookup/dry-run-preview', dom_ready_slice)

    def test_batch_local_preview_endpoint_exists(self):
        resp = self.client.post('/api/operator/actual-result-lookup/batch/guarded-local-preview', json={})
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data.get('mode'), 'batch_local_preview')

    def test_batch_local_preview_rejects_empty_selected_keys(self):
        resp = self.client.post('/api/operator/actual-result-lookup/batch/guarded-local-preview', json={
            'selected_keys': [],
            'mode': 'local_only',
            'approval_granted': False,
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('selected_keys', data.get('error') or '')

    def test_batch_local_preview_rejects_duplicate_selected_keys(self):
        selected_key = 'dup_key|path'
        resp = self.client.post('/api/operator/actual-result-lookup/batch/guarded-local-preview', json={
            'selected_keys': [selected_key, selected_key],
            'mode': 'local_only',
            'approval_granted': False,
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('duplicates', (data.get('error') or '').lower())

    def test_batch_local_preview_rejects_more_than_hard_cap(self):
        resp = self.client.post('/api/operator/actual-result-lookup/batch/guarded-local-preview', json={
            'selected_keys': ['k1', 'k2', 'k3', 'k4', 'k5', 'k6'],
            'mode': 'local_only',
            'approval_granted': False,
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('hard cap', (data.get('error') or '').lower())

    def test_batch_local_preview_rejects_approval_true(self):
        resp = self.client.post('/api/operator/actual-result-lookup/batch/guarded-local-preview', json={
            'selected_keys': ['k1'],
            'mode': 'local_only',
            'approval_granted': True,
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('preview-only', (data.get('error') or '').lower())

    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_batch_local_preview_valid_selection_returns_no_mutation_and_token(self, mock_summary, mock_local_map):
        selected_key = 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Alpha vs Beta',
                'predicted_winner': 'Alpha',
                'event_date': '2026-01-01',
                'file_path': 'predictions/alpha_vs_beta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        mock_local_map.return_value = ({
            'alpha_vs_beta': {
                'record': {
                    'fight_id': 'alpha_vs_beta',
                    'actual_winner': 'alpha',
                    'actual_method': 'Decision',
                    'actual_round': '3',
                    'event_date': '2026-01-01',
                },
                'source_file': 'actual_results_manual.json',
            }
        }, Path(__file__).resolve().parent.parent / 'ops' / 'accuracy')

        before = self._actual_results_file_hashes()
        resp = self.client.post('/api/operator/actual-result-lookup/batch/guarded-local-preview', json={
            'selected_keys': [selected_key],
            'mode': 'local_only',
            'approval_granted': False,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('mode'), 'batch_local_preview')
        self.assertEqual(data.get('batch_size_requested'), 1)
        self.assertEqual(data.get('batch_size_accepted'), 1)
        self.assertEqual(data.get('hard_cap'), 5)
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertFalse(data.get('scoring_semantics_changed'))
        self.assertIsInstance(data.get('rows'), list)
        self.assertTrue(data.get('execution_token'))
        self.assertGreater(int(data.get('token_ttl_seconds') or 0), 0)

        after = self._actual_results_file_hashes()
        self.assertEqual(before, after)

    def test_advanced_dashboard_has_batch_local_preview_controls(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'operator-batch-local-preview-btn', resp.data)
        self.assertIn(b'operator-batch-local-preview-output', resp.data)
        self.assertIn(b'/api/operator/actual-result-lookup/batch/guarded-local-preview', resp.data)
        self.assertIn(b'Preview only. No web lookup, no result write, no scoring change.', resp.data)

    def test_advanced_batch_local_preview_not_called_on_page_load(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')

        dom_ready_start = page.find("window.addEventListener('DOMContentLoaded', () => {")
        self.assertNotEqual(dom_ready_start, -1)
        dom_ready_slice = page[dom_ready_start:dom_ready_start + 1800]
        self.assertNotIn('/api/operator/actual-result-lookup/batch/guarded-local-preview', dom_ready_slice)

    def test_guarded_single_lookup_endpoint_exists(self):
        resp = self.client.post('/api/operator/actual-result-lookup/guarded-single', json={'selected_key': 'missing|missing'})
        self.assertIn(resp.status_code, (200, 404))
        data = resp.get_json()
        self.assertIn('mode', data)
        self.assertEqual(data.get('mode'), 'guarded_single_lookup')

    def test_guarded_single_lookup_missing_selected_key_returns_400_no_mutation(self):
        before = self._actual_results_file_hashes()
        resp = self.client.post('/api/operator/actual-result-lookup/guarded-single', json={})
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('ok'))
        self.assertEqual(data.get('mode'), 'guarded_single_lookup')
        self.assertTrue(data.get('approval_required'))
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        after = self._actual_results_file_hashes()
        self.assertEqual(before, after)

    def test_guarded_single_lookup_unknown_selected_key_returns_404_manual_review_no_mutation(self):
        before = self._actual_results_file_hashes()
        resp = self.client.post('/api/operator/actual-result-lookup/guarded-single', json={
            'selected_key': 'unknown_fight|unknown_path',
            'approval_granted': False,
        })
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertFalse(data.get('ok'))
        self.assertEqual(data.get('mode'), 'guarded_single_lookup')
        self.assertTrue(data.get('approval_required'))
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertTrue(data.get('manual_review_required'))
        after = self._actual_results_file_hashes()
        self.assertEqual(before, after)

    @patch('app._load_json_records')
    @patch('app._build_accuracy_comparison_summary')
    def test_guarded_single_lookup_approval_false_never_mutates(self, mock_summary, mock_load_json_records):
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Alpha vs Beta',
                'predicted_winner': 'Alpha',
                'event_date': '2026-01-01',
                'file_path': 'predictions/alpha_vs_beta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }

        def _fake_load(_path):
            return [{
                'fight_id': 'alpha_vs_beta',
                'actual_winner': 'alpha',
                'actual_method': 'Decision',
                'actual_round': '3',
                'event_date': '2026-01-01',
                'source': 'manual',
            }]

        mock_load_json_records.side_effect = _fake_load

        before = self._actual_results_file_hashes()
        resp = self.client.post('/api/operator/actual-result-lookup/guarded-single', json={
            'selected_key': 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json',
            'approval_granted': False,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertTrue(data.get('approval_required'))
        self.assertFalse(data.get('approval_granted'))
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertTrue(data.get('local_result_found'))
        self.assertIn('proposed_write', data)
        after = self._actual_results_file_hashes()
        self.assertEqual(before, after)

    @patch('app._load_json_records', return_value=[])
    @patch('app._build_accuracy_comparison_summary')
    def test_guarded_single_lookup_approval_true_no_local_result_no_mutation(self, mock_summary, _mock_load_json_records):
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Gamma vs Delta',
                'predicted_winner': 'Gamma',
                'event_date': '2026-01-02',
                'file_path': 'predictions/gamma_vs_delta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }

        before = self._actual_results_file_hashes()
        resp = self.client.post('/api/operator/actual-result-lookup/guarded-single', json={
            'selected_key': 'gamma_vs_delta|predictions_gamma_vs_delta_prediction_json',
            'approval_granted': True,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertTrue(data.get('approval_required'))
        self.assertTrue(data.get('approval_granted'))
        self.assertFalse(data.get('local_result_found'))
        self.assertTrue(data.get('manual_review_required'))
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertIn('No local actual result found', data.get('message') or '')
        after = self._actual_results_file_hashes()
        self.assertEqual(before, after)

    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_guarded_single_lookup_approval_true_local_result_writes_once_with_audit(self, mock_summary, mock_load_local_map):
        selected_key = 'don_madge_vs_tba_prediction|predictions_don_madge_vs_tba_prediction_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'don_madge_vs_tba_prediction',
                'predicted_winner': 'don_madge',
                'event_date': 'UNKNOWN',
                'file_path': 'predictions/don_madge_vs_tba_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }

        repo_hash_before = self._actual_results_file_hashes()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            accuracy_dir = tmp_root / 'ops' / 'accuracy'
            accuracy_dir.mkdir(parents=True, exist_ok=True)

            manual_path = accuracy_dir / 'actual_results_manual.json'
            manual_path.write_text('[]\n', encoding='utf-8')
            (accuracy_dir / 'actual_results.json').write_text('[]\n', encoding='utf-8')
            (accuracy_dir / 'actual_results_unresolved.json').write_text('[]\n', encoding='utf-8')

            local_actual = {
                'fight_id': 'don_madge_vs_tba',
                'actual_winner': 'don_madge',
                'actual_method': 'TKO',
                'actual_round': '1',
                'event_date': '2023-08-05',
                'source': 'manual',
            }
            mock_load_local_map.return_value = ({
                'don_madge_vs_tba': {
                    'record': local_actual,
                    'source_file': 'actual_results_manual.json',
                }
            }, accuracy_dir)

            resp = self.client.post('/api/operator/actual-result-lookup/guarded-single', json={
                'selected_key': selected_key,
                'approval_granted': True,
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self.assertTrue(data.get('ok'))
            self.assertTrue(data.get('approval_required'))
            self.assertTrue(data.get('approval_granted'))
            self.assertTrue(data.get('local_result_found'))
            self.assertFalse(data.get('manual_review_required'))
            self.assertTrue(data.get('mutation_performed'))
            self.assertEqual(data.get('resolved_count'), 1)
            self.assertFalse(data.get('external_lookup_performed'))
            self.assertFalse(data.get('bulk_lookup_performed'))
            self.assertFalse(data.get('scoring_semantics_changed'))

            audit = data.get('audit') or {}
            self.assertTrue(audit.get('write_performed'))
            self.assertEqual(audit.get('write_action'), 'insert_or_update_single_record')
            self.assertEqual(audit.get('selected_key'), selected_key)
            self.assertEqual(audit.get('matched_local_source_file'), 'actual_results_manual.json')
            self.assertEqual(audit.get('record_fight_id'), 'don_madge_vs_tba')
            self.assertEqual(audit.get('write_target'), str(manual_path))

            before_count = int(audit.get('before_row_count'))
            after_count = int(audit.get('after_row_count'))
            self.assertIn(after_count - before_count, (0, 1))

            written_rows = json.loads(manual_path.read_text(encoding='utf-8'))
            matched_rows = [row for row in written_rows if row.get('fight_id') == 'don_madge_vs_tba']
            self.assertEqual(len(matched_rows), 1)

        repo_hash_after = self._actual_results_file_hashes()
        self.assertEqual(repo_hash_before, repo_hash_after)

    def test_official_source_one_record_preview_endpoint_exists(self):
        resp = self.client.post('/api/operator/actual-result-lookup/official-source-one-record-preview', json={})
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data.get('mode'), 'official_source_one_record')
        self.assertEqual(data.get('phase'), 'lookup_preview')

    def test_official_source_approved_apply_endpoint_exists(self):
        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json={})
        self.assertIn(resp.status_code, (200, 400))
        data = resp.get_json()
        self.assertEqual(data.get('mode'), 'official_source_approved_apply')
        self.assertEqual(data.get('phase'), 'approved_apply')

    def test_official_source_approved_apply_non_json_or_malformed_json_rejected_without_mutation(self):
        before = self._actual_results_file_hashes()

        non_json_resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-approved-apply',
            data='not-json',
            content_type='text/plain',
        )
        self.assertEqual(non_json_resp.status_code, 400)
        non_json_data = non_json_resp.get_json()
        self._assert_approved_apply_normalized_envelope(non_json_data)
        self.assertFalse(non_json_data.get('request_valid'))
        self.assertFalse(non_json_data.get('mutation_performed'))

        malformed_json_resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-approved-apply',
            data='{"bad_json": ',
            content_type='application/json',
        )
        self.assertEqual(malformed_json_resp.status_code, 400)
        malformed_json_data = malformed_json_resp.get_json()
        self._assert_approved_apply_normalized_envelope(malformed_json_data)
        self.assertFalse(malformed_json_data.get('request_valid'))
        self.assertFalse(malformed_json_data.get('mutation_performed'))

        after = self._actual_results_file_hashes()
        self.assertEqual(before, after)

    def test_official_source_approved_apply_invalid_schema_returns_request_invalid(self):
        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json={
            'mode': 'official_source_approved_apply',
            'lookup_intent': 'apply_write',
            'selected_key': '',
            'approval_granted': True,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertFalse(data.get('request_valid'))
        self.assertFalse(data.get('guard_allowed'))
        self.assertFalse(data.get('mutation_performed'))

    def test_official_source_approved_apply_invalid_mode_returns_normalized_envelope(self):
        payload = self._official_approved_apply_payload(mode='official_source_one_record')
        payload['approval_token'] = self._issue_approved_apply_token(payload)
        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertFalse(data.get('request_valid'))
        self.assertEqual(data.get('reason_code'), 'invalid_apply_mode')

    def test_official_source_approved_apply_invalid_lookup_intent_returns_normalized_envelope(self):
        payload = self._official_approved_apply_payload(lookup_intent='preview_only')
        payload['approval_token'] = self._issue_approved_apply_token(payload)
        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertFalse(data.get('request_valid'))
        self.assertEqual(data.get('reason_code'), 'invalid_lookup_intent')

    def test_official_source_approved_apply_rejects_batch_fields(self):
        payload = self._official_approved_apply_payload(selected_keys=['k1'], queue_wide=True)
        payload['approval_token'] = self._issue_approved_apply_token(payload)
        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertFalse(data.get('request_valid'))
        self.assertFalse(data.get('guard_allowed'))
        self.assertEqual(data.get('reason_code'), 'batch_field_not_allowed')

    def test_official_source_approved_apply_missing_token_rejected(self):
        payload = self._official_approved_apply_payload()
        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertFalse(data.get('request_valid'))
        self.assertFalse(data.get('token_valid'))
        self.assertFalse(data.get('guard_allowed'))

    def test_official_source_approved_apply_token_binding_mismatch_rejected(self):
        payload = self._official_approved_apply_payload()
        payload['approval_token'] = self._issue_approved_apply_token(payload)
        payload['approval_binding']['source_date'] = '1999-01-01'
        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertFalse(data.get('token_valid'))
        self.assertFalse(data.get('guard_allowed'))
        self.assertEqual(data.get('reason_code'), 'approval_binding_mismatch')

    def test_official_source_approved_apply_valid_payload_returns_guard_allowed_true(self):
        payload = self._official_approved_apply_payload()
        payload['approval_token'] = self._issue_approved_apply_token(payload)
        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertTrue(data.get('request_valid'))
        self.assertTrue(data.get('token_valid'))
        self.assertTrue(data.get('guard_allowed'))
        self.assertTrue(data.get('approval_required'))
        self.assertTrue(data.get('approval_granted'))
        self.assertTrue(data.get('approval_binding_valid'))
        self.assertEqual(data.get('token_status'), 'valid')
        self.assertEqual(data.get('approval_token_status'), 'valid')
        self.assertIsNone(data.get('operation_id'))

    def test_official_source_approved_apply_with_operation_id_surfaces_on_success_response(self):
        payload = self._official_approved_apply_payload(operation_id='  op_retry_20260430_abcdef  ')
        payload['approval_token'] = self._issue_approved_apply_token(payload)

        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()

        self._assert_approved_apply_normalized_envelope(data)
        self.assertTrue(data.get('guard_allowed'))
        self.assertEqual(data.get('reason_code'), 'mutation_disabled_after_guard')
        self.assertEqual(data.get('operation_id'), 'op_retry_20260430_abcdef')

    def test_official_source_approved_apply_without_operation_id_remains_backward_compatible_and_no_audit_row(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_path = Path(temp_dir) / 'approved_apply_operation_id_audit.jsonl'
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE'] = str(audit_path)

            payload = self._official_approved_apply_payload()
            payload['approval_token'] = self._issue_approved_apply_token(payload)

            resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self._assert_approved_apply_normalized_envelope(data)
            self.assertEqual(data.get('reason_code'), 'mutation_disabled_after_guard')
            self.assertIsNone(data.get('operation_id'))
            self.assertEqual(self._read_operation_id_audit_rows(audit_path), [])

    def test_official_source_approved_apply_first_operation_id_request_records_append_only_audit_row(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_path = Path(temp_dir) / 'approved_apply_operation_id_audit.jsonl'
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE'] = str(audit_path)

            payload = self._official_approved_apply_payload(operation_id='op_retry_20260430_abcdef')
            payload['approval_token'] = self._issue_approved_apply_token(payload)

            resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            rows = self._read_operation_id_audit_rows(audit_path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(data.get('operation_id'), 'op_retry_20260430_abcdef')
            self.assertEqual(rows[0].get('operation_id'), 'op_retry_20260430_abcdef')
            self.assertIsNone(rows[0].get('internal_mutation_operation_id'))
            self.assertEqual(rows[0].get('request_parse_status'), 'schema_valid')
            self.assertEqual(rows[0].get('guard_or_authorization_outcome'), 'guard_allowed')
            self.assertEqual(rows[0].get('apply_or_write_outcome'), 'not_attempted')
            self.assertEqual(rows[0].get('token_consume_outcome'), 'not_attempted')
            self.assertEqual(rows[0].get('deterministic_status'), 'guard_allowed_no_write')

    def test_official_source_approved_apply_retry_after_success_is_deterministic_and_does_not_double_apply(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_accuracy_dir = Path(temp_dir) / 'accuracy'
            temp_accuracy_dir.mkdir()
            temp_manual_path = temp_accuracy_dir / 'actual_results_manual.json'
            temp_manual_path.write_text('[]\n', encoding='utf-8')
            audit_path = Path(temp_dir) / 'approved_apply_operation_id_audit.jsonl'

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE'] = str(audit_path)

            payload = self._official_approved_apply_payload(operation_id='op_retry_20260430_abcdef')
            payload['approval_token'] = self._issue_approved_apply_token(payload)

            first_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(first_resp.status_code, 200)
            first_data = first_resp.get_json()
            self.assertTrue(first_data.get('write_performed'))

            second_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(second_resp.status_code, 200)
            second_data = second_resp.get_json()
            self.assertEqual(second_data.get('reason_code'), 'operation_id_already_applied')
            self.assertFalse(second_data.get('write_performed'))
            self.assertFalse(second_data.get('mutation_performed'))

            rows = self._read_operation_id_audit_rows(audit_path)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0].get('deterministic_status'), 'write_applied')
            self.assertEqual(rows[1].get('deterministic_status'), 'already_applied_replay')
            self.assertNotEqual(rows[0].get('internal_mutation_operation_id'), payload.get('operation_id'))
            self.assertEqual(rows[1].get('internal_mutation_operation_id'), rows[0].get('internal_mutation_operation_id'))

            manual_rows = json.loads(temp_manual_path.read_text(encoding='utf-8'))
            matched_rows = [row for row in manual_rows if row.get('fight_id') == 'alpha_vs_beta']
            self.assertEqual(len(matched_rows), 1)

    def test_official_source_approved_apply_retry_after_deny_is_deterministic_and_does_not_bypass_guard(self):
        real_guard = app_module.evaluate_official_source_approved_apply_guard
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_path = Path(temp_dir) / 'approved_apply_operation_id_audit.jsonl'
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE'] = str(audit_path)

            payload = self._official_approved_apply_payload(operation_id='op_retry_20260430_abcdef')
            payload['preview_snapshot']['source_citation']['source_confidence'] = 'tier_b'
            payload['preview_snapshot']['source_citation']['confidence_score'] = 0.55
            payload['preview_snapshot']['acceptance_gate']['state'] = 'manual_review'
            payload['preview_snapshot']['acceptance_gate']['write_eligible'] = False
            payload['preview_snapshot']['acceptance_gate']['reason_code'] = 'tier_b_without_corroboration'
            payload['approval_token'] = self._issue_approved_apply_token(payload)

            with patch('app.evaluate_official_source_approved_apply_guard', side_effect=real_guard) as mock_guard:
                first_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
                second_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)

            self.assertEqual(mock_guard.call_count, 2)
            first_data = first_resp.get_json()
            second_data = second_resp.get_json()
            self.assertFalse(first_data.get('guard_allowed'))
            self.assertFalse(second_data.get('guard_allowed'))
            self.assertEqual(first_data.get('reason_code'), second_data.get('reason_code'))

            rows = self._read_operation_id_audit_rows(audit_path)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0].get('deterministic_status'), 'guard_denied')
            self.assertEqual(rows[1].get('deterministic_status'), 'guard_denied')

    def test_official_source_approved_apply_duplicate_operation_id_conflict_is_handled_deterministically(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_path = Path(temp_dir) / 'approved_apply_operation_id_audit.jsonl'
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE'] = str(audit_path)

            first_payload = self._official_approved_apply_payload(operation_id='op_retry_20260430_abcdef')
            first_payload['approval_token'] = self._issue_approved_apply_token(first_payload)
            first_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=first_payload)
            self.assertEqual(first_resp.status_code, 200)

            second_payload = self._official_approved_apply_payload(
                selected_key='gamma_vs_delta|predictions_gamma_vs_delta_prediction_json',
                operation_id='op_retry_20260430_abcdef',
            )
            second_payload['approval_token'] = self._issue_approved_apply_token(second_payload)
            second_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=second_payload)
            self.assertEqual(second_resp.status_code, 200)
            second_data = second_resp.get_json()

            self.assertFalse(second_data.get('guard_allowed'))
            self.assertEqual(second_data.get('reason_code'), 'operation_id_conflict')
            self.assertFalse(second_data.get('write_performed'))

            rows = self._read_operation_id_audit_rows(audit_path)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0].get('deterministic_status'), 'guard_allowed_no_write')
            self.assertEqual(rows[1].get('deterministic_status'), 'duplicate_conflict')

    def test_official_source_approved_apply_malformed_operation_id_does_not_corrupt_audit_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_path = Path(temp_dir) / 'approved_apply_operation_id_audit.jsonl'
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE'] = str(audit_path)

            payload = self._official_approved_apply_payload(operation_id='short-id')
            payload['approval_token'] = self._issue_approved_apply_token(payload)
            resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self.assertFalse(data.get('request_valid'))
            self.assertEqual(data.get('reason_code'), 'operation_id_format_invalid')
            self.assertEqual(self._read_operation_id_audit_rows(audit_path), [])

    def test_official_source_approved_apply_with_operation_id_surfaces_on_deny_response(self):
        payload = self._official_approved_apply_payload(mode='official_source_one_record', operation_id='  op_retry_20260430_abcdef  ')
        payload['approval_token'] = self._issue_approved_apply_token(payload)

        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()

        self._assert_approved_apply_normalized_envelope(data)
        self.assertFalse(data.get('request_valid'))
        self.assertFalse(data.get('guard_allowed'))
        self.assertEqual(data.get('reason_code'), 'invalid_apply_mode')
        self.assertEqual(data.get('operation_id'), 'op_retry_20260430_abcdef')

    def test_official_source_approved_apply_operation_id_does_not_change_token_binding(self):
        payload = self._official_approved_apply_payload(operation_id='op_retry_20260430_abcdef')
        payload['approval_token'] = self._issue_approved_apply_token(payload)

        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()

        self._assert_approved_apply_normalized_envelope(data)
        self.assertTrue(data.get('request_valid'))
        self.assertTrue(data.get('token_valid'))
        self.assertTrue(data.get('approval_binding_valid'))
        self.assertEqual(data.get('operation_id'), 'op_retry_20260430_abcdef')

    def test_official_source_approved_apply_guard_allowed_true_still_non_mutating_flags(self):
        payload = self._official_approved_apply_payload()
        payload['approval_token'] = self._issue_approved_apply_token(payload)
        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertTrue(data.get('guard_allowed'))
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('write_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertFalse(data.get('scoring_semantics_changed'))
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertFalse(data.get('mutation_enabled'))
        self.assertEqual(data.get('reason_code'), 'mutation_disabled_after_guard')

    @patch('app.OFFICIAL_SOURCE_APPROVED_APPLY_TOKEN_CONSUME_HELPER.register_consume')
    @patch('app.apply_official_source_approved_apply_mutation')
    def test_official_source_approved_apply_default_disabled_never_calls_adapter_or_consume(self, mock_apply, mock_consume):
        payload = self._official_approved_apply_payload()
        payload['approval_token'] = self._issue_approved_apply_token(payload)

        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertTrue(data.get('guard_allowed'))
        self.assertFalse(data.get('mutation_enabled'))
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('write_performed'))
        self.assertFalse(data.get('token_consume_performed'))
        self.assertEqual(data.get('reason_code'), 'mutation_disabled_after_guard')

        mock_apply.assert_not_called()
        mock_consume.assert_not_called()

    @patch('app.OFFICIAL_SOURCE_APPROVED_APPLY_TOKEN_CONSUME_HELPER.register_consume')
    @patch('app.apply_official_source_approved_apply_mutation')
    def test_official_source_approved_apply_guard_deny_never_calls_adapter(self, mock_apply, mock_consume):
        app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
        payload = self._official_approved_apply_payload()

        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertFalse(data.get('guard_allowed'))
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('write_performed'))

        mock_apply.assert_not_called()
        mock_consume.assert_not_called()

    @patch('app.OFFICIAL_SOURCE_APPROVED_APPLY_TOKEN_CONSUME_HELPER.register_consume')
    @patch('app.apply_official_source_approved_apply_mutation')
    def test_official_source_approved_apply_enabled_without_accuracy_override_fails_closed(self, mock_apply, mock_consume):
        app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
        app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = None

        payload = self._official_approved_apply_payload()
        payload['approval_token'] = self._issue_approved_apply_token(payload)

        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertTrue(data.get('mutation_enabled'))
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('write_performed'))
        self.assertFalse(data.get('token_consume_performed'))
        self.assertEqual(data.get('reason_code'), 'mutation_accuracy_dir_not_configured')

        mock_apply.assert_not_called()
        mock_consume.assert_not_called()

    def test_official_source_approved_apply_enabled_temp_path_writes_only_temp_manual_results(self):
        repo_hash_before = self._actual_results_file_hashes()
        payload = self._official_approved_apply_payload()
        payload['approval_token'] = self._issue_approved_apply_token(payload)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_accuracy_dir = Path(temp_dir)
            temp_manual_path = temp_accuracy_dir / 'actual_results_manual.json'
            temp_manual_path.write_text('[]\n', encoding='utf-8')

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)

            resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self._assert_approved_apply_normalized_envelope(data)
            self.assertTrue(data.get('mutation_enabled'))
            self.assertTrue(data.get('mutation_performed'))
            self.assertTrue(data.get('write_performed'))
            self.assertEqual(Path(data.get('write_target')), temp_manual_path)
            self.assertEqual(temp_manual_path.name, 'actual_results_manual.json')

            rows = json.loads(temp_manual_path.read_text(encoding='utf-8'))
            matched_rows = [row for row in rows if row.get('fight_id') == 'alpha_vs_beta']
            self.assertEqual(len(matched_rows), 1)

        repo_hash_after = self._actual_results_file_hashes()
        self.assertEqual(repo_hash_before, repo_hash_after)

    def test_official_source_approved_apply_temp_write_becomes_visible_to_accuracy_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            temp_accuracy_dir.mkdir()
            (temp_accuracy_dir / 'actual_results.json').write_text('[]\n', encoding='utf-8')
            (temp_accuracy_dir / 'actual_results_manual.json').write_text('[]\n', encoding='utf-8')
            (temp_accuracy_dir / 'actual_results_unresolved.json').write_text('[]\n', encoding='utf-8')
            (temp_accuracy_dir / 'accuracy_ledger.json').write_text(json.dumps([
                {
                    'fight_id': 'alpha_vs_beta',
                    'predicted_winner': 'Alpha',
                    'event_date': '2024-01-01',
                    'source_file': 'predictions/alpha_vs_beta_prediction.json',
                }
            ]), encoding='utf-8')
            audit_path = temp_root / 'approved_apply_operation_id_audit.jsonl'
            ledger_path = temp_root / 'approved_apply_global_ledger.jsonl'

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE'] = str(audit_path)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)

            before_resp = self.client.get('/api/accuracy/comparison-summary')
            self.assertEqual(before_resp.status_code, 200)
            before_data = before_resp.get_json()
            waiting_before = [row for row in before_data.get('waiting_for_results') or [] if row.get('fight_name') == 'alpha_vs_beta']
            self.assertEqual(len(waiting_before), 1)

            payload = self._official_approved_apply_payload(operation_id='op_retry_20260430_abcdef')
            payload['approval_token'] = self._issue_approved_apply_token(payload)

            apply_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(apply_resp.status_code, 200)
            apply_data = apply_resp.get_json()
            self.assertTrue(apply_data.get('write_performed'))
            self.assertTrue(apply_data.get('mutation_performed'))
            self.assertEqual(apply_data.get('operation_id'), 'op_retry_20260430_abcdef')

            after_resp = self.client.get('/api/accuracy/comparison-summary')
            self.assertEqual(after_resp.status_code, 200)
            after_data = after_resp.get_json()
            waiting_after = [row for row in after_data.get('waiting_for_results') or [] if row.get('fight_name') == 'alpha_vs_beta']
            compared_after = [row for row in after_data.get('compared_results') or [] if row.get('fight_name') == 'alpha_vs_beta']
            self.assertEqual(waiting_after, [])
            self.assertEqual(len(compared_after), 1)
            self.assertEqual(compared_after[0].get('actual_winner'), 'Alpha')
            self.assertEqual(compared_after[0].get('status'), 'compared')

            manual_rows = json.loads((temp_accuracy_dir / 'actual_results_manual.json').read_text(encoding='utf-8'))
            matched_rows = [row for row in manual_rows if row.get('fight_id') == 'alpha_vs_beta']
            self.assertEqual(len(matched_rows), 1)

            audit_rows = self._read_operation_id_audit_rows(audit_path)
            self.assertEqual(len(audit_rows), 1)
            self.assertEqual(audit_rows[0].get('operation_id'), 'op_retry_20260430_abcdef')
            self.assertEqual(audit_rows[0].get('deterministic_status'), 'write_applied')

            ledger_rows = self._read_global_ledger_rows(ledger_path)
            self.assertEqual(len(ledger_rows), 1)
            self.assertEqual(ledger_rows[0].get('local_result_key'), 'alpha_vs_beta')
            self.assertEqual(ledger_rows[0].get('operation_id'), 'op_retry_20260430_abcdef')
            self.assertNotEqual(ledger_rows[0].get('internal_mutation_uuid'), payload.get('operation_id'))
            self.assertEqual(ledger_rows[0].get('approved_actual_result', {}).get('actual_winner'), 'Alpha')

    def test_official_source_approved_apply_guard_deny_leaves_local_summary_waiting_and_audits_operation_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            temp_accuracy_dir.mkdir()
            (temp_accuracy_dir / 'actual_results.json').write_text('[]\n', encoding='utf-8')
            (temp_accuracy_dir / 'actual_results_manual.json').write_text('[]\n', encoding='utf-8')
            (temp_accuracy_dir / 'actual_results_unresolved.json').write_text('[]\n', encoding='utf-8')
            (temp_accuracy_dir / 'accuracy_ledger.json').write_text(json.dumps([
                {
                    'fight_id': 'alpha_vs_beta',
                    'predicted_winner': 'Alpha',
                    'event_date': '2024-01-01',
                    'source_file': 'predictions/alpha_vs_beta_prediction.json',
                }
            ]), encoding='utf-8')
            audit_path = temp_root / 'approved_apply_operation_id_audit.jsonl'
            ledger_path = temp_root / 'approved_apply_global_ledger.jsonl'

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE'] = str(audit_path)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)

            payload = self._official_approved_apply_payload(operation_id='op_retry_20260430_abcdef')
            payload['preview_snapshot']['source_citation']['source_confidence'] = 'tier_b'
            payload['preview_snapshot']['source_citation']['confidence_score'] = 0.55
            payload['preview_snapshot']['acceptance_gate']['state'] = 'manual_review'
            payload['preview_snapshot']['acceptance_gate']['write_eligible'] = False
            payload['preview_snapshot']['acceptance_gate']['reason_code'] = 'tier_b_without_corroboration'
            payload['approval_token'] = self._issue_approved_apply_token(payload)

            apply_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(apply_resp.status_code, 200)
            apply_data = apply_resp.get_json()
            self.assertFalse(apply_data.get('guard_allowed'))
            self.assertFalse(apply_data.get('write_performed'))
            self.assertFalse(apply_data.get('mutation_performed'))
            self.assertEqual(apply_data.get('operation_id'), 'op_retry_20260430_abcdef')

            manual_rows = json.loads((temp_accuracy_dir / 'actual_results_manual.json').read_text(encoding='utf-8'))
            self.assertEqual(manual_rows, [])

            summary_resp = self.client.get('/api/accuracy/comparison-summary')
            self.assertEqual(summary_resp.status_code, 200)
            summary_data = summary_resp.get_json()
            waiting_rows = [row for row in summary_data.get('waiting_for_results') or [] if row.get('fight_name') == 'alpha_vs_beta']
            compared_rows = [row for row in summary_data.get('compared_results') or [] if row.get('fight_name') == 'alpha_vs_beta']
            self.assertEqual(len(waiting_rows), 1)
            self.assertEqual(compared_rows, [])

            audit_rows = self._read_operation_id_audit_rows(audit_path)
            self.assertEqual(len(audit_rows), 1)
            self.assertEqual(audit_rows[0].get('operation_id'), 'op_retry_20260430_abcdef')
            self.assertEqual(audit_rows[0].get('deterministic_status'), 'guard_denied')
            self.assertEqual(self._read_global_ledger_rows(ledger_path), [])

    def test_official_source_approved_apply_success_mirrors_once_to_global_ledger_without_operation_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            temp_accuracy_dir.mkdir()
            temp_manual_path = temp_accuracy_dir / 'actual_results_manual.json'
            temp_manual_path.write_text('[]\n', encoding='utf-8')
            ledger_path = temp_root / 'approved_apply_global_ledger.jsonl'

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)

            payload = self._official_approved_apply_payload()
            payload['approval_token'] = self._issue_approved_apply_token(payload)

            resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self.assertTrue(data.get('write_performed'))
            self.assertIsNone(data.get('operation_id'))

            ledger_rows = self._read_global_ledger_rows(ledger_path)
            self.assertEqual(len(ledger_rows), 1)
            self.assertIsNone(ledger_rows[0].get('operation_id'))
            self.assertEqual(ledger_rows[0].get('local_result_key'), 'alpha_vs_beta')

            manual_rows = json.loads(temp_manual_path.read_text(encoding='utf-8'))
            matched_rows = [row for row in manual_rows if row.get('fight_id') == 'alpha_vs_beta']
            self.assertEqual(len(matched_rows), 1)

    def test_official_source_approved_apply_duplicate_global_ledger_same_payload_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            temp_accuracy_dir.mkdir()
            temp_manual_path = temp_accuracy_dir / 'actual_results_manual.json'
            temp_manual_path.write_text('[]\n', encoding='utf-8')
            ledger_path = temp_root / 'approved_apply_global_ledger.jsonl'

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)

            payload = self._official_approved_apply_payload()
            payload['approval_token'] = self._issue_approved_apply_token(payload)

            first_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(first_resp.status_code, 200)
            self.assertTrue(first_resp.get_json().get('write_performed'))

            second_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(second_resp.status_code, 200)
            second_data = second_resp.get_json()
            self.assertEqual(second_data.get('reason_code'), 'global_ledger_already_recorded')
            self.assertFalse(second_data.get('write_performed'))
            self.assertFalse(second_data.get('mutation_performed'))

            ledger_rows = self._read_global_ledger_rows(ledger_path)
            self.assertEqual(len(ledger_rows), 1)

            manual_rows = json.loads(temp_manual_path.read_text(encoding='utf-8'))
            matched_rows = [row for row in manual_rows if row.get('fight_id') == 'alpha_vs_beta']
            self.assertEqual(len(matched_rows), 1)

    def test_official_source_approved_apply_duplicate_global_ledger_conflict_returns_explicit_conflict(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            temp_accuracy_dir.mkdir()
            temp_manual_path = temp_accuracy_dir / 'actual_results_manual.json'
            temp_manual_path.write_text('[]\n', encoding='utf-8')
            ledger_path = temp_root / 'approved_apply_global_ledger.jsonl'

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)

            first_payload = self._official_approved_apply_payload()
            first_payload['approval_token'] = self._issue_approved_apply_token(first_payload)
            first_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=first_payload)
            self.assertEqual(first_resp.status_code, 200)
            self.assertTrue(first_resp.get_json().get('write_performed'))

            second_payload = self._official_approved_apply_payload()
            second_payload['approval_binding'] = dict(second_payload['approval_binding'])
            second_payload['preview_snapshot'] = dict(second_payload['preview_snapshot'])
            second_payload['preview_snapshot']['source_citation'] = dict(second_payload['preview_snapshot']['source_citation'])
            second_payload['preview_snapshot']['source_citation']['extracted_winner'] = 'Beta'
            second_payload['approval_binding']['extracted_winner'] = 'Beta'
            second_payload['approval_token'] = self._issue_approved_apply_token(second_payload)

            second_resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=second_payload)
            self.assertEqual(second_resp.status_code, 200)
            second_data = second_resp.get_json()
            self.assertEqual(second_data.get('reason_code'), 'global_ledger_conflict')
            self.assertFalse(second_data.get('token_consume_performed'))

            ledger_rows = self._read_global_ledger_rows(ledger_path)
            self.assertEqual(len(ledger_rows), 1)
            self.assertEqual(ledger_rows[0].get('approved_actual_result', {}).get('actual_winner'), 'Alpha')

            manual_rows = json.loads(temp_manual_path.read_text(encoding='utf-8'))
            matched_rows = [row for row in manual_rows if row.get('fight_id') == 'alpha_vs_beta']
            self.assertEqual(len(matched_rows), 1)
            self.assertEqual(matched_rows[0].get('actual_winner'), 'Alpha')

    def test_official_source_approved_apply_global_ledger_write_failure_does_not_corrupt_local_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            temp_accuracy_dir.mkdir()
            temp_manual_path = temp_accuracy_dir / 'actual_results_manual.json'
            temp_manual_path.write_text('[]\n', encoding='utf-8')
            ledger_path = temp_root / 'approved_apply_global_ledger.jsonl'

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)

            payload = self._official_approved_apply_payload()
            payload['approval_token'] = self._issue_approved_apply_token(payload)

            with patch('app.OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_HELPER.append_record', side_effect=OSError('global ledger unavailable')):
                resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)

            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data.get('write_performed'))
            self.assertFalse(data.get('token_consume_performed'))
            self.assertEqual(data.get('reason_code'), 'global_ledger_write_failed')
            self.assertEqual(self._read_global_ledger_rows(ledger_path), [])

            manual_rows = json.loads(temp_manual_path.read_text(encoding='utf-8'))
            matched_rows = [row for row in manual_rows if row.get('fight_id') == 'alpha_vs_beta']
            self.assertEqual(len(matched_rows), 1)

    def test_global_ledger_summary_endpoint_returns_safe_empty_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            temp_accuracy_dir.mkdir()
            ledger_path = temp_root / 'approved_apply_global_ledger.jsonl'

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)

            resp = self.client.get('/api/operator/actual-result-lookup/global-ledger-summary')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            for key in ('ok', 'generated_at', 'ledger_available', 'total_rows', 'latest_rows', 'status_counts', 'errors'):
                self.assertIn(key, data)
            self.assertTrue(data.get('ok'))
            self.assertFalse(data.get('ledger_available'))
            self.assertEqual(data.get('total_rows'), 0)
            self.assertEqual(data.get('latest_rows'), [])
            self.assertEqual(data.get('status_counts'), {})
            self.assertEqual(data.get('errors'), [])

    def test_global_ledger_summary_endpoint_latest_rows_and_status_counts_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            temp_accuracy_dir.mkdir()
            ledger_path = temp_root / 'approved_apply_global_ledger.jsonl'

            rows = [
                {
                    'global_ledger_record_id': 'r1',
                    'local_result_key': 'fight_alpha',
                    'event_id': 'evt1',
                    'bout_id': 'bout1',
                    'official_source_reference': {'source_url': 'https://ufc.com/event/1'},
                    'approved_actual_result': {'actual_winner': 'Alpha'},
                    'operation_id': 'op1',
                    'deterministic_status': 'write_applied',
                    'timestamp_utc': '2026-01-01T00:00:00Z',
                    'local_audit_reference': {'selected_key': 'fight_alpha|predictions_1'},
                },
                {
                    'global_ledger_record_id': 'r2',
                    'local_result_key': 'fight_beta',
                    'event_id': 'evt2',
                    'bout_id': 'bout2',
                    'official_source_reference': {'source_url': 'https://ufc.com/event/2'},
                    'approved_actual_result': {'actual_winner': 'Beta'},
                    'operation_id': None,
                    'deterministic_status': 'global_ledger_already_recorded',
                    'timestamp_utc': '2026-01-02T00:00:00Z',
                    'local_audit_reference': {'selected_key': 'fight_beta|predictions_2'},
                },
                {
                    'global_ledger_record_id': 'r3',
                    'local_result_key': 'fight_gamma',
                    'event_id': 'evt3',
                    'bout_id': 'bout3',
                    'official_source_reference': {'source_url': 'https://ufc.com/event/3'},
                    'approved_actual_result': {'actual_winner': 'Gamma'},
                    'operation_id': 'op3',
                    'deterministic_status': 'global_ledger_write_failed',
                    'timestamp_utc': '2026-01-03T00:00:00Z',
                    'local_audit_reference': {'selected_key': 'fight_gamma|predictions_3'},
                },
            ]
            ledger_path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)

            first_resp = self.client.get('/api/operator/actual-result-lookup/global-ledger-summary?limit=2')
            second_resp = self.client.get('/api/operator/actual-result-lookup/global-ledger-summary?limit=2')
            self.assertEqual(first_resp.status_code, 200)
            self.assertEqual(second_resp.status_code, 200)

            first_data = first_resp.get_json()
            second_data = second_resp.get_json()
            self.assertEqual(first_data.get('latest_rows'), second_data.get('latest_rows'))

            self.assertTrue(first_data.get('ledger_available'))
            self.assertEqual(first_data.get('total_rows'), 3)
            self.assertEqual(len(first_data.get('latest_rows') or []), 2)
            self.assertEqual(first_data['latest_rows'][0].get('global_ledger_record_id'), 'r3')
            self.assertEqual(first_data['latest_rows'][1].get('global_ledger_record_id'), 'r2')
            self.assertEqual(first_data.get('status_counts'), {
                'global_ledger_already_recorded': 1,
                'global_ledger_write_failed': 1,
                'write_applied': 1,
            })

            row_keys = set(first_data['latest_rows'][0].keys())
            expected_row_keys = {
                'global_ledger_record_id',
                'local_result_key',
                'event_id',
                'bout_id',
                'official_source_reference',
                'approved_actual_result',
                'operation_id',
                'deterministic_status',
                'timestamp_utc',
                'local_audit_reference',
            }
            self.assertEqual(row_keys, expected_row_keys)

    def test_global_ledger_summary_endpoint_reports_malformed_rows_without_breaking_response(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            temp_accuracy_dir.mkdir()
            ledger_path = temp_root / 'approved_apply_global_ledger.jsonl'

            lines = [
                json.dumps({
                    'global_ledger_record_id': 'r1',
                    'local_result_key': 'fight_alpha',
                    'deterministic_status': 'write_applied',
                    'timestamp_utc': '2026-01-01T00:00:00Z',
                }),
                '{ malformed json',
                json.dumps(['not', 'an', 'object']),
                json.dumps({
                    'global_ledger_record_id': 'r2',
                    'local_result_key': 'fight_beta',
                    'deterministic_status': 'global_ledger_already_recorded',
                    'timestamp_utc': '2026-01-02T00:00:00Z',
                }),
            ]
            ledger_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)

            resp = self.client.get('/api/operator/actual-result-lookup/global-ledger-summary')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self.assertTrue(data.get('ok'))
            self.assertTrue(data.get('ledger_available'))
            self.assertEqual(data.get('total_rows'), 2)
            self.assertEqual(len(data.get('latest_rows') or []), 2)
            self.assertGreaterEqual(len(data.get('errors') or []), 2)
            error_text = ' | '.join(data.get('errors') or [])
            self.assertIn('malformed_row_line_2', error_text)
            self.assertIn('malformed_row_line_3', error_text)

    def test_advanced_dashboard_has_global_ledger_read_only_panel(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Approved-Apply Global Ledger (Read-Only)', resp.data)
        self.assertIn(b'refresh-global-ledger-summary-btn', resp.data)
        self.assertIn(b'global-ledger-summary-panel', resp.data)
        self.assertIn(b'/api/operator/actual-result-lookup/global-ledger-summary', resp.data)
        self.assertIn(b'No write controls', resp.data)

    def test_advanced_dashboard_has_report_scoring_bridge_readiness_panel(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Report-Scoring Bridge Readiness', resp.data)
        self.assertIn(b'refresh-report-scoring-bridge-summary-btn', resp.data)
        self.assertIn(b'report-scoring-bridge-summary-panel', resp.data)

    def test_advanced_dashboard_wires_report_scoring_bridge_summary_endpoint(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/operator/report-scoring-bridge/summary', resp.data)

    def test_advanced_dashboard_report_scoring_bridge_panel_has_no_write_controls(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')
        panel_start = page.find('Report-Scoring Bridge Readiness')
        self.assertNotEqual(panel_start, -1)
        panel_slice = page[panel_start:panel_start + 2200]
        self.assertIn('Read-only visibility only. No write controls, no token consume, no approval-token display.', page)
        self.assertNotIn('Apply', panel_slice)
        self.assertNotIn('approval_token', panel_slice)
        self.assertNotIn('token_digest', panel_slice)

    def test_advanced_dashboard_report_scoring_bridge_panel_has_empty_and_error_surfaces(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'No bridge records available.', resp.data)
        self.assertIn(b'Malformed/parse issues:', resp.data)

    def test_advanced_dashboard_report_scoring_bridge_panel_has_latest_and_status_render_path(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Status counts', resp.data)
        self.assertIn(b'Latest records', resp.data)
        self.assertIn(b'score_outcome', resp.data)
        self.assertIn(b'scoring_bridge_status', resp.data)
        self.assertIn(b'duplicate_conflict', resp.data)
        self.assertIn(b'mismatch', resp.data)
        self.assertIn(b'unresolved', resp.data)

    @patch('app.OFFICIAL_SOURCE_APPROVED_APPLY_TOKEN_CONSUME_HELPER.register_consume')
    def test_official_source_approved_apply_token_consume_called_only_after_successful_write(self, mock_consume):
        mock_consume.return_value = {
            'ok': True,
            'token_consume_performed': True,
            'reason_code': 'consumed',
            'idempotent': False,
            'errors': [],
        }
        payload = self._official_approved_apply_payload(operation_id='op_retry_20260430_abcdef')
        payload['approval_token'] = self._issue_approved_apply_token(payload)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_accuracy_dir = Path(temp_dir)
            audit_path = temp_accuracy_dir / 'approved_apply_operation_id_audit.jsonl'
            ledger_path = temp_accuracy_dir / 'approved_apply_global_ledger.jsonl'
            (temp_accuracy_dir / 'actual_results_manual.json').write_text('[]\n', encoding='utf-8')
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_OPERATION_ID_AUDIT_PATH_OVERRIDE'] = str(audit_path)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)

            resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data.get('write_performed'))
            self.assertTrue(data.get('token_consume_performed'))
            rows = self._read_operation_id_audit_rows(audit_path)
            self.assertEqual(len(rows), 1)
            ledger_rows = self._read_global_ledger_rows(ledger_path)
            self.assertEqual(len(ledger_rows), 1)

        self.assertEqual(mock_consume.call_count, 1)
        call_args = mock_consume.call_args
        self.assertEqual(call_args.args[0], data.get('token_id'))
        self.assertEqual(call_args.kwargs.get('selected_key'), data.get('selected_key'))
        self.assertEqual(call_args.kwargs.get('binding_digest_expected'), data.get('binding_digest_expected'))
        self.assertEqual(call_args.kwargs.get('contract_version'), 'official_source_approved_apply_contract_v1')
        self.assertEqual(call_args.kwargs.get('endpoint_version'), 'official_source_approved_apply_endpoint_mutation_v1')
        self.assertEqual(data.get('operation_id'), 'op_retry_20260430_abcdef')
        self.assertNotEqual(call_args.kwargs.get('operation_id'), data.get('operation_id'))
        self.assertEqual(len(call_args.kwargs.get('operation_id') or ''), 32)
        self.assertEqual(call_args.kwargs.get('write_attempt_id'), data.get('write_attempt_id'))
        self.assertEqual(rows[0].get('internal_mutation_operation_id'), call_args.kwargs.get('operation_id'))
        self.assertEqual(ledger_rows[0].get('internal_mutation_uuid'), call_args.kwargs.get('operation_id'))

    def test_official_source_approved_apply_consume_failure_after_write_keeps_committed_temp_write(self):
        payload = self._official_approved_apply_payload()
        payload['approval_token'] = self._issue_approved_apply_token(payload)
        adapter_call_count = {'count': 0}
        real_adapter_apply = app_module.apply_official_source_approved_apply_mutation

        def wrapped_adapter(*args, **kwargs):
            adapter_call_count['count'] += 1
            return real_adapter_apply(*args, **kwargs)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_accuracy_dir = Path(temp_dir)
            temp_manual_path = temp_accuracy_dir / 'actual_results_manual.json'
            temp_manual_path.write_text('[]\n', encoding='utf-8')

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_MUTATION_ENABLED'] = True
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)

            with patch('app.apply_official_source_approved_apply_mutation', side_effect=wrapped_adapter):
                with patch(
                    'app.OFFICIAL_SOURCE_APPROVED_APPLY_TOKEN_CONSUME_HELPER.register_consume',
                    return_value={
                        'ok': False,
                        'token_consume_performed': False,
                        'reason_code': 'token_consume_store_unavailable',
                        'idempotent': False,
                        'errors': ['token consume store unavailable'],
                    },
                ):
                    resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)

            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data.get('write_performed'))
            self.assertTrue(data.get('mutation_performed'))
            self.assertFalse(data.get('token_consume_performed'))
            self.assertEqual(data.get('reason_code'), 'token_consume_post_write_failed')
            self.assertEqual(data.get('token_consume_reason_code'), 'token_consume_store_unavailable')
            self.assertEqual(adapter_call_count['count'], 1)

            rows = json.loads(temp_manual_path.read_text(encoding='utf-8'))
            matched_rows = [row for row in rows if row.get('fight_id') == 'alpha_vs_beta']
            self.assertEqual(len(matched_rows), 1)

    def test_official_source_approved_apply_manual_review_gate_returns_guard_denied(self):
        payload = self._official_approved_apply_payload()
        payload['preview_snapshot']['source_citation']['source_confidence'] = 'tier_b'
        payload['preview_snapshot']['source_citation']['confidence_score'] = 0.55
        payload['preview_snapshot']['acceptance_gate']['state'] = 'manual_review'
        payload['preview_snapshot']['acceptance_gate']['write_eligible'] = False
        payload['preview_snapshot']['acceptance_gate']['reason_code'] = 'tier_b_without_corroboration'
        payload['approval_token'] = self._issue_approved_apply_token(payload)

        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertFalse(data.get('guard_allowed'))

    def test_official_source_approved_apply_rejected_gate_returns_guard_denied(self):
        payload = self._official_approved_apply_payload()
        payload['preview_snapshot']['reason_code'] = 'identity_conflict'
        payload['preview_snapshot']['acceptance_gate']['state'] = 'rejected'
        payload['preview_snapshot']['acceptance_gate']['write_eligible'] = False
        payload['preview_snapshot']['acceptance_gate']['reason_code'] = 'identity_conflict'
        payload['approval_token'] = self._issue_approved_apply_token(payload)

        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self._assert_approved_apply_normalized_envelope(data)
        self.assertFalse(data.get('guard_allowed'))

    @patch('app._upsert_single_manual_actual_result')
    def test_official_source_approved_apply_never_calls_upsert(self, mock_upsert):
        payload = self._official_approved_apply_payload()
        payload['approval_token'] = self._issue_approved_apply_token(payload)
        resp = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        self.assertEqual(resp.status_code, 200)
        mock_upsert.assert_not_called()

    def test_official_source_approved_apply_keeps_actual_results_json_unchanged(self):
        root = Path(__file__).resolve().parent.parent / 'ops' / 'accuracy'
        target = str(root / 'actual_results.json')
        before = self._actual_results_file_hashes()
        payload = self._official_approved_apply_payload()
        payload['approval_token'] = self._issue_approved_apply_token(payload)
        _ = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        after = self._actual_results_file_hashes()
        self.assertEqual(before[target], after[target])

    def test_official_source_approved_apply_keeps_actual_results_manual_json_unchanged(self):
        root = Path(__file__).resolve().parent.parent / 'ops' / 'accuracy'
        target = str(root / 'actual_results_manual.json')
        before = self._actual_results_file_hashes()
        payload = self._official_approved_apply_payload()
        payload['approval_token'] = self._issue_approved_apply_token(payload)
        _ = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        after = self._actual_results_file_hashes()
        self.assertEqual(before[target], after[target])

    def test_official_source_approved_apply_keeps_actual_results_unresolved_json_unchanged(self):
        root = Path(__file__).resolve().parent.parent / 'ops' / 'accuracy'
        target = str(root / 'actual_results_unresolved.json')
        before = self._actual_results_file_hashes()
        payload = self._official_approved_apply_payload()
        payload['approval_token'] = self._issue_approved_apply_token(payload)
        _ = self.client.post('/api/operator/actual-result-lookup/official-source-approved-apply', json=payload)
        after = self._actual_results_file_hashes()
        self.assertEqual(before[target], after[target])

    def test_official_source_approved_apply_no_dashboard_template_changes(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(b'/api/operator/actual-result-lookup/official-source-approved-apply', resp.data)

    def test_official_source_one_record_preview_missing_selected_key_rejected(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(selected_key=''),
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('selected_key is required', data.get('error') or '')

    def test_official_source_one_record_preview_selected_key_array_rejected(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(selected_key=['bad', 'shape']),
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('selected_key must be a string', data.get('error') or '')

    def test_official_source_one_record_preview_mode_mismatch_rejected(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(mode='local_only'),
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('mode must be official_source_one_record', data.get('error') or '')

    def test_official_source_one_record_preview_lookup_intent_mismatch_rejected(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(lookup_intent='apply_now'),
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('lookup_intent must be preview_only', data.get('error') or '')

    def test_official_source_one_record_preview_approval_true_rejected(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(approval_granted=True),
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('approval_granted must be false', data.get('error') or '')

    def test_official_source_one_record_preview_batch_like_fields_rejected(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(selected_keys=['one'], targets=['two']),
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('not allowed', data.get('error') or '')

    @patch('app.OfficialSourceLookupProvider')
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_official_source_preview_candidate_urls_absent_preserves_v1b_behavior(self, mock_summary, mock_local_map, mock_provider_cls):
        selected_key = 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Alpha vs Beta',
                'predicted_winner': 'Alpha',
                'event_date': '2026-01-01',
                'file_path': 'predictions/alpha_vs_beta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        mock_local_map.return_value = ({}, Path(__file__).resolve().parent.parent / 'ops' / 'accuracy')
        mock_provider_cls.return_value.run_preview_lookup.return_value = {
            'provider_attempted': True,
            'external_lookup_performed': False,
            'source_citation': None,
            'manual_review_required': True,
            'reason_code': 'no_acceptable_official_source_found',
            'attempted_sources': [],
            'timeout_budget_seconds': 20,
            'per_source_timeout_seconds': 6,
            'auto_retry_count': 0,
        }

        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(selected_key=selected_key),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertFalse(data.get('candidate_urls_supplied'))
        self.assertEqual(data.get('candidate_url_count'), 0)

        kwargs = mock_provider_cls.return_value.run_preview_lookup.call_args.kwargs
        self.assertIn('candidate_urls', kwargs)
        self.assertIsNone(kwargs.get('candidate_urls'))

    def test_official_source_preview_candidate_urls_non_list_rejected(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(candidate_urls='https://ufc.com/event/test-card'),
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('candidate_urls must be a list', data.get('error') or '')

    def test_official_source_preview_candidate_urls_empty_rejected(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(candidate_urls=[]),
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data.get('reason_code'), 'candidate_urls_empty')

    def test_official_source_preview_candidate_urls_exceeds_limit_rejected(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(candidate_urls=[
                'https://ufc.com/event/one',
                'https://ufc.com/event/two',
                'https://ufc.com/event/three',
                'https://ufc.com/event/four',
            ]),
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data.get('reason_code'), 'candidate_urls_exceeds_limit')

    def test_official_source_preview_candidate_urls_non_https_rejected(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(candidate_urls=['http://ufc.com/event/test-card']),
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data.get('reason_code'), 'source_url_not_allowed')

    def test_official_source_preview_candidate_urls_shortener_rejected(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(candidate_urls=['https://bit.ly/test-card']),
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data.get('reason_code'), 'source_url_not_allowed')

    @patch('app.OfficialSourceLookupProvider')
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_official_source_preview_candidate_urls_deduped_deterministically(self, mock_summary, mock_local_map, mock_provider_cls):
        selected_key = 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Alpha vs Beta',
                'predicted_winner': 'Alpha',
                'event_date': '2026-01-01',
                'file_path': 'predictions/alpha_vs_beta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        mock_local_map.return_value = ({}, Path(__file__).resolve().parent.parent / 'ops' / 'accuracy')
        mock_provider_cls.return_value.run_preview_lookup.return_value = {
            'provider_attempted': True,
            'external_lookup_performed': False,
            'source_citation': None,
            'manual_review_required': True,
            'reason_code': 'no_acceptable_official_source_found',
            'attempted_sources': [],
            'timeout_budget_seconds': 20,
            'per_source_timeout_seconds': 6,
            'auto_retry_count': 0,
            'candidate_urls_supplied': True,
            'candidate_url_count': 2,
        }

        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(
                selected_key=selected_key,
                candidate_urls=[
                    'https://ufc.com/event/test-card',
                    ' https://ufc.com/event/test-card ',
                    'https://onefc.com/events/test-card',
                ],
            ),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('candidate_urls_supplied'))
        self.assertEqual(data.get('candidate_url_count'), 2)

        kwargs = mock_provider_cls.return_value.run_preview_lookup.call_args.kwargs
        self.assertEqual(kwargs.get('candidate_urls'), [
            'https://ufc.com/event/test-card',
            'https://onefc.com/events/test-card',
        ])

    @patch('app._upsert_single_manual_actual_result')
    @patch('app.OfficialSourceLookupProvider')
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_official_source_preview_candidate_urls_valid_can_return_accepted_preview(self, mock_summary, mock_local_map, mock_provider_cls, mock_upsert):
        selected_key = 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Alpha vs Beta',
                'predicted_winner': 'Alpha',
                'event_date': '2026-01-01',
                'file_path': 'predictions/alpha_vs_beta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        mock_local_map.return_value = ({}, Path(__file__).resolve().parent.parent / 'ops' / 'accuracy')
        mock_provider_cls.return_value.run_preview_lookup.return_value = {
            'provider_attempted': True,
            'external_lookup_performed': True,
            'source_citation': {
                'source_url': 'https://ufc.com/event/test-card',
                'source_title': 'UFC Test Card',
                'source_date': '2026-01-01',
                'publisher_host': 'ufc.com',
                'source_confidence': 'tier_a0',
                'confidence_score': 0.85,
                'citation_fingerprint': 'abc123',
                'extracted_winner': 'Alpha',
                'method': 'DECISION',
                'round_time': 'R3 5:00',
            },
            'manual_review_required': False,
            'reason_code': 'accepted_preview',
            'attempted_sources': ['https://ufc.com/event/test-card'],
            'timeout_budget_seconds': 20,
            'per_source_timeout_seconds': 6,
            'auto_retry_count': 0,
            'candidate_urls_supplied': True,
            'candidate_url_count': 1,
        }

        before_hashes = self._actual_results_file_hashes()
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(
                selected_key=selected_key,
                candidate_urls=['https://ufc.com/event/test-card'],
            ),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get('reason_code'), 'accepted_preview')
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertFalse(data.get('scoring_semantics_changed'))
        self.assertTrue(data.get('candidate_urls_supplied'))
        self.assertEqual(data.get('candidate_url_count'), 1)
        self.assertIsNotNone(data.get('source_citation'))
        mock_upsert.assert_not_called()
        self.assertEqual(before_hashes, self._actual_results_file_hashes())

    def test_ui_candidate_urls_textarea_present(self):
        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        self.assertIn(b'id="operator-official-source-candidate-urls"', advanced_resp.data)

    def test_ui_candidate_urls_in_post_body_js(self):
        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        self.assertIn(b'candidate_urls', advanced_resp.data)

    def test_ui_render_shows_candidate_urls_supplied(self):
        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        self.assertIn(b'candidate_urls_supplied', advanced_resp.data)

    def test_ui_render_shows_candidate_url_count(self):
        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        self.assertIn(b'candidate_url_count', advanced_resp.data)

    def test_ui_render_shows_acceptance_gate_fields(self):
        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        self.assertIn(b'Acceptance Gate', advanced_resp.data)
        self.assertIn(b'acceptance_gate', advanced_resp.data)
        self.assertIn(b'acceptanceGate.state', advanced_resp.data)
        self.assertIn(b'acceptanceGate.reason_code', advanced_resp.data)
        self.assertIn(b'acceptanceGate.write_eligible', advanced_resp.data)
        self.assertIn(b'acceptanceGate.checks', advanced_resp.data)
        self.assertIn(b'acceptanceGate.citation_fingerprint', advanced_resp.data)

    def test_ui_render_shows_acceptance_gate_fallback_text(self):
        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        self.assertIn(b'Not available', advanced_resp.data)

    def test_ui_maximum_3_safety_text_present(self):
        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        self.assertIn(b'Maximum 3', advanced_resp.data)

    def test_no_official_source_preview_on_domcontentloaded(self):
        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        html = advanced_resp.data.decode('utf-8')
        # The preview URL must only appear inside the onclick handler,
        # not as a top-level auto-call from DOMContentLoaded.
        # Structural proof: the onclick assignment appears before the fetch call
        # in document order, so preview_url_pos > onclick_pos must hold.
        preview_url = '/api/operator/actual-result-lookup/official-source-one-record-preview'
        onclick_anchor = 'officialSourcePreviewBtn.onclick'
        self.assertIn(preview_url, html, 'preview URL must appear in template (inside onclick)')
        self.assertIn(onclick_anchor, html, 'officialSourcePreviewBtn.onclick must be wired in template')
        onclick_pos = html.find(onclick_anchor)
        preview_url_pos = html.find(preview_url)
        self.assertGreater(preview_url_pos, onclick_pos,
            'official-source preview endpoint must only appear inside onclick handler, not as an auto-call')

    def test_no_write_apply_wording_introduced(self):
        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        # Confirm no new write/apply capability was wired into the candidate URL textarea
        html = advanced_resp.data.decode('utf-8')
        textarea_pos = html.find('operator-official-source-candidate-urls')
        self.assertGreater(textarea_pos, 0)
        # The panel disclaimer "No write" must still be present
        self.assertIn('No write', html)

    def test_no_batch_behavior_introduced(self):
        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        html = advanced_resp.data.decode('utf-8')
        # No batch-specific attribute added to the candidate URLs textarea
        textarea_pos = html.find('operator-official-source-candidate-urls')
        self.assertGreater(textarea_pos, 0)
        # The panel disclaimer "no batch" must still be present
        self.assertIn('no batch', html)

    @patch('app._upsert_single_manual_actual_result')
    @patch('app.OfficialSourceLookupProvider')
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_official_source_one_record_preview_valid_selected_key_returns_preview_only_flags(self, mock_summary, mock_local_map, mock_provider_cls, mock_upsert):
        selected_key = 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Alpha vs Beta',
                'predicted_winner': 'Alpha',
                'event_date': '2026-01-01',
                'file_path': 'predictions/alpha_vs_beta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        mock_local_map.return_value = ({}, Path(__file__).resolve().parent.parent / 'ops' / 'accuracy')
        mock_provider = mock_provider_cls.return_value
        mock_provider.run_preview_lookup.return_value = {
            'provider_attempted': True,
            'external_lookup_performed': True,
            'source_citation': {
                'source_url': 'https://ufc.com/event/test-card',
                'source_title': 'UFC Test Card',
                'source_date': datetime.now(timezone.utc).date().isoformat(),
                'publisher_host': 'ufc.com',
                'source_confidence': 'tier_a0',
                'confidence_score': 0.85,
                'citation_fingerprint': 'abc123',
                'extracted_winner': 'Alpha',
                'method': 'DECISION',
                'round_time': 'R3 5:00',
            },
            'manual_review_required': False,
            'reason_code': 'accepted_preview',
            'attempted_sources': ['https://ufc.com/event/test-card'],
            'timeout_budget_seconds': 20,
            'per_source_timeout_seconds': 6,
            'auto_retry_count': 0,
        }

        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(selected_key=selected_key),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('mode'), 'official_source_one_record')
        self.assertEqual(data.get('phase'), 'lookup_preview')
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertFalse(data.get('scoring_semantics_changed'))
        self.assertTrue(data.get('external_lookup_performed'))
        self.assertFalse(data.get('manual_review_required'))
        self.assertFalse(data.get('local_result_found'))
        self.assertIsNone(data.get('proposed_write'))
        self.assertIsNotNone(data.get('source_citation'))
        self.assertEqual((data.get('audit') or {}).get('reason_code'), 'accepted_preview')
        self.assertEqual((data.get('acceptance_gate') or {}).get('state'), 'write_eligible')
        self.assertEqual((data.get('acceptance_gate') or {}).get('reason_code'), 'accepted_preview_write_eligible')
        mock_provider.run_preview_lookup.assert_called_once()
        mock_upsert.assert_not_called()

    @patch('app._upsert_single_manual_actual_result')
    @patch('app.OfficialSourceLookupProvider')
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_official_source_one_record_preview_local_result_found_still_does_not_mutate(self, mock_summary, mock_local_map, mock_provider_cls, mock_upsert):
        selected_key = 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Alpha vs Beta',
                'predicted_winner': 'Alpha',
                'event_date': '2026-01-01',
                'file_path': 'predictions/alpha_vs_beta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        mock_local_map.return_value = ({
            'alpha_vs_beta': {
                'record': {
                    'fight_id': 'alpha_vs_beta',
                    'actual_winner': 'Alpha',
                    'actual_method': 'Decision',
                    'actual_round': '3',
                    'event_date': '2026-01-01',
                },
                'source_file': 'actual_results_manual.json',
            }
        }, Path(__file__).resolve().parent.parent / 'ops' / 'accuracy')

        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(selected_key=selected_key),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertFalse(data.get('scoring_semantics_changed'))
        self.assertTrue(data.get('local_result_found'))
        self.assertFalse(data.get('manual_review_required'))
        self.assertIsNone(data.get('proposed_write'))
        self.assertIn('did not mutate', data.get('message') or '')
        self.assertEqual((data.get('acceptance_gate') or {}).get('state'), 'rejected')
        self.assertEqual((data.get('acceptance_gate') or {}).get('reason_code'), 'citation_incomplete')
        mock_provider_cls.assert_not_called()
        mock_upsert.assert_not_called()

    @patch('app.OfficialSourceLookupProvider')
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_official_source_one_record_preview_local_result_not_found_calls_provider_once(self, mock_summary, mock_local_map, mock_provider_cls):
        selected_key = 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Alpha vs Beta',
                'predicted_winner': 'Alpha',
                'event_date': '2026-01-01',
                'file_path': 'predictions/alpha_vs_beta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        mock_local_map.return_value = ({}, Path(__file__).resolve().parent.parent / 'ops' / 'accuracy')
        mock_provider_cls.return_value.run_preview_lookup.return_value = {
            'provider_attempted': True,
            'external_lookup_performed': False,
            'source_citation': None,
            'manual_review_required': True,
            'reason_code': 'no_acceptable_official_source_found',
            'attempted_sources': [],
            'timeout_budget_seconds': 20,
            'per_source_timeout_seconds': 6,
            'auto_retry_count': 0,
        }

        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(selected_key=selected_key),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('manual_review_required'))
        self.assertEqual((data.get('acceptance_gate') or {}).get('state'), 'rejected')
        self.assertEqual((data.get('acceptance_gate') or {}).get('reason_code'), 'citation_incomplete')
        mock_provider_cls.return_value.run_preview_lookup.assert_called_once()

    @patch('app._upsert_single_manual_actual_result')
    @patch('app.OfficialSourceLookupProvider')
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_official_source_one_record_preview_reason_code_matrix_is_forwarded(self, mock_summary, mock_local_map, mock_provider_cls, mock_upsert):
        selected_key = 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Alpha vs Beta',
                'predicted_winner': 'Alpha',
                'event_date': '2026-01-01',
                'file_path': 'predictions/alpha_vs_beta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        mock_local_map.return_value = ({}, Path(__file__).resolve().parent.parent / 'ops' / 'accuracy')

        reason_codes = [
            'tier_b_without_corroboration',
            'citation_incomplete',
            'source_url_not_allowed',
            'publisher_host_mismatch',
            'timeout_budget_exceeded',
            'source_conflict_same_tier',
            'source_conflict',
            'identity_conflict',
            'no_acceptable_official_source_found',
        ]
        for reason_code in reason_codes:
            source_citation = None
            if reason_code == 'tier_b_without_corroboration':
                source_citation = {
                    'source_url': 'https://www.espn.com/mma/fight/_/id/test-card',
                    'source_title': 'ESPN Test Card',
                    'source_date': datetime.now(timezone.utc).date().isoformat(),
                    'publisher_host': 'www.espn.com',
                    'source_confidence': 'tier_b',
                    'confidence_score': 0.55,
                    'citation_fingerprint': 'tierb123',
                    'extracted_winner': 'Alpha',
                    'method': None,
                    'round_time': None,
                    'identity_matches_selected_row': True,
                }
            mock_provider_cls.return_value.run_preview_lookup.return_value = {
                'provider_attempted': True,
                'external_lookup_performed': reason_code != 'no_acceptable_official_source_found',
                'source_citation': source_citation,
                'manual_review_required': True,
                'reason_code': reason_code,
                'attempted_sources': ['https://example.com/source'],
                'timeout_budget_seconds': 20,
                'per_source_timeout_seconds': 6,
                'auto_retry_count': 0,
            }
            resp = self.client.post(
                '/api/operator/actual-result-lookup/official-source-one-record-preview',
                json=self._official_preview_payload(selected_key=selected_key),
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertEqual((data.get('audit') or {}).get('reason_code'), reason_code)
            self.assertTrue(data.get('manual_review_required'))

            acceptance_gate = data.get('acceptance_gate') or {}
            if reason_code == 'tier_b_without_corroboration':
                self.assertEqual(acceptance_gate.get('state'), 'manual_review')
                self.assertEqual(acceptance_gate.get('reason_code'), 'tier_b_without_corroboration')
            else:
                self.assertEqual(acceptance_gate.get('state'), 'rejected')
                self.assertEqual(acceptance_gate.get('reason_code'), 'citation_incomplete')

        mock_upsert.assert_not_called()

    @patch('app.OfficialSourceLookupProvider')
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_official_source_one_record_preview_stale_source_date_reason_code(self, mock_summary, mock_local_map, mock_provider_cls):
        selected_key = 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Alpha vs Beta',
                'predicted_winner': 'Alpha',
                'event_date': '2026-01-01',
                'file_path': 'predictions/alpha_vs_beta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        mock_local_map.return_value = ({}, Path(__file__).resolve().parent.parent / 'ops' / 'accuracy')
        mock_provider_cls.return_value.run_preview_lookup.return_value = {
            'provider_attempted': True,
            'external_lookup_performed': True,
            'source_citation': {
                'source_url': 'https://ufc.com/event/test-card',
                'source_title': 'UFC Test Card',
                'source_date': '2020-01-01',
                'publisher_host': 'ufc.com',
                'source_confidence': 'tier_a0',
                'confidence_score': 0.85,
                'citation_fingerprint': 'fp1',
                'extracted_winner': 'Alpha',
                'method': None,
                'round_time': None,
            },
            'manual_review_required': True,
            'reason_code': 'stale_source_date',
            'attempted_sources': ['https://ufc.com/event/test-card'],
            'timeout_budget_seconds': 20,
            'per_source_timeout_seconds': 6,
            'auto_retry_count': 0,
        }

        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(selected_key=selected_key),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual((data.get('audit') or {}).get('reason_code'), 'stale_source_date')
        self.assertTrue(data.get('manual_review_required'))
        self.assertEqual((data.get('acceptance_gate') or {}).get('state'), 'manual_review')
        self.assertEqual((data.get('acceptance_gate') or {}).get('reason_code'), 'stale_source_date')

    def test_official_source_one_record_preview_selected_key_not_found_includes_acceptance_gate(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(selected_key='unknown_fight|unknown_path'),
        )
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertEqual(data.get('reason_code'), 'selected_key_not_found')
        self.assertEqual((data.get('acceptance_gate') or {}).get('state'), 'rejected')
        self.assertEqual((data.get('acceptance_gate') or {}).get('reason_code'), 'citation_incomplete')

    def test_official_source_one_record_preview_does_not_change_actual_results_files(self):
        before = self._actual_results_file_hashes()
        resp = self.client.post(
            '/api/operator/actual-result-lookup/official-source-one-record-preview',
            json=self._official_preview_payload(selected_key='unknown_fight|unknown_path'),
        )
        self.assertEqual(resp.status_code, 404)
        after = self._actual_results_file_hashes()
        root = Path(__file__).resolve().parent.parent / 'ops' / 'accuracy'
        self.assertEqual(before[str(root / 'actual_results.json')], after[str(root / 'actual_results.json')])
        self.assertEqual(before[str(root / 'actual_results_manual.json')], after[str(root / 'actual_results_manual.json')])
        self.assertEqual(before[str(root / 'actual_results_unresolved.json')], after[str(root / 'actual_results_unresolved.json')])

    def test_provider_disallowed_host_returns_source_url_not_allowed(self):
        provider = OfficialSourceLookupProvider(
            search_provider=lambda _q: ['https://bad.example.com/result'],
            fetch_provider=lambda _url, _timeout: {
                'final_url': 'https://bad.example.com/result',
                'title': 'Unknown Result',
                'source_date': '2026-01-01',
                'html': '<html><body>Alpha defeated Beta</body></html>',
            },
        )
        result = provider.run_preview_lookup(
            selected_key='alpha|beta',
            selected_row={'fight_name': 'Alpha vs Beta'},
        )
        self.assertTrue(result.get('manual_review_required'))
        self.assertEqual(result.get('reason_code'), 'source_url_not_allowed')

    def test_provider_redirect_final_host_mismatch_returns_publisher_host_mismatch(self):
        provider = OfficialSourceLookupProvider(
            search_provider=lambda _q: ['https://ufc.com/event/test-card'],
            fetch_provider=lambda _url, _timeout: {
                'final_url': 'https://bit.ly/wrapped',
                'title': 'UFC Test Card',
                'source_date': '2026-01-01',
                'html': '<html><body>Alpha defeated Beta</body></html>',
            },
        )
        result = provider.run_preview_lookup(
            selected_key='alpha|beta',
            selected_row={'fight_name': 'Alpha vs Beta'},
        )
        self.assertEqual(result.get('reason_code'), 'publisher_host_mismatch')

    def test_provider_timeout_returns_timeout_budget_exceeded(self):
        provider = OfficialSourceLookupProvider(
            search_provider=lambda _q: ['https://ufc.com/event/test-card'],
            fetch_provider=lambda _url, _timeout: (_ for _ in ()).throw(TimeoutError('timeout')),
        )
        result = provider.run_preview_lookup(
            selected_key='alpha|beta',
            selected_row={'fight_name': 'Alpha vs Beta'},
        )
        self.assertEqual(result.get('reason_code'), 'timeout_budget_exceeded')

    def test_provider_conflict_returns_source_conflict_same_tier(self):
        calls = {'count': 0}

        def _fetch(_url, _timeout):
            calls['count'] += 1
            if calls['count'] == 1:
                html = '<html><body>Alpha defeated Beta</body></html>'
            else:
                html = '<html><body>Beta defeated Alpha</body></html>'
            return {
                'final_url': 'https://ufc.com/event/test-card',
                'title': 'UFC Test Card',
                'source_date': '2026-01-01',
                'html': html,
            }

        provider = OfficialSourceLookupProvider(
            search_provider=lambda _q: ['https://ufc.com/event/test-card', 'https://www.ufc.com/event/another-card'],
            fetch_provider=_fetch,
            now_provider=lambda: datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
        result = provider.run_preview_lookup(
            selected_key='alpha|beta',
            selected_row={'fight_name': 'Alpha vs Beta'},
        )
        self.assertEqual(result.get('reason_code'), 'source_conflict_same_tier')

    def test_provider_identity_mismatch_returns_identity_conflict(self):
        provider = OfficialSourceLookupProvider(
            search_provider=lambda _q: ['https://ufc.com/event/test-card'],
            fetch_provider=lambda _url, _timeout: {
                'final_url': 'https://ufc.com/event/test-card',
                'title': 'UFC Test Card',
                'source_date': '2026-01-01',
                'html': '<html><body>Gamma defeated Delta by decision in round 3</body></html>',
            },
            now_provider=lambda: datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
        result = provider.run_preview_lookup(
            selected_key='alpha|beta',
            selected_row={'fight_name': 'Alpha vs Beta'},
        )
        self.assertEqual(result.get('reason_code'), 'identity_conflict')

    def test_provider_tier_b_only_returns_manual_review(self):
        provider = OfficialSourceLookupProvider(
            search_provider=lambda _q: ['https://tapology.com/fightcenter/events/test-card'],
            fetch_provider=lambda _url, _timeout: {
                'final_url': 'https://tapology.com/fightcenter/events/test-card',
                'title': 'Tapology Card',
                'source_date': '2026-01-01',
                'html': '<html><body>Alpha defeated Beta by decision in round 3</body></html>',
            },
            now_provider=lambda: datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
        result = provider.run_preview_lookup(
            selected_key='alpha|beta',
            selected_row={'fight_name': 'Alpha vs Beta'},
        )
        self.assertTrue(result.get('manual_review_required'))
        self.assertEqual(result.get('reason_code'), 'tier_b_without_corroboration')

    def test_provider_incomplete_citation_returns_citation_incomplete(self):
        provider = OfficialSourceLookupProvider(
            search_provider=lambda _q: ['https://ufc.com/event/test-card'],
            fetch_provider=lambda _url, _timeout: {
                'final_url': 'https://ufc.com/event/test-card',
                'title': '',
                'source_date': '',
                'html': '<html><body>Alpha defeated Beta</body></html>',
            },
        )
        result = provider.run_preview_lookup(
            selected_key='alpha|beta',
            selected_row={'fight_name': 'Alpha vs Beta'},
        )
        self.assertEqual(result.get('reason_code'), 'citation_incomplete')

    def test_provider_no_acceptable_source_returns_no_acceptable_official_source_found(self):
        provider = OfficialSourceLookupProvider(
            search_provider=lambda _q: [],
            fetch_provider=lambda _url, _timeout: {},
            now_provider=lambda: datetime.now(timezone.utc),
        )
        result = provider.run_preview_lookup(
            selected_key='alpha|beta',
            selected_row={'fight_name': 'Alpha vs Beta'},
        )
        self.assertEqual(result.get('reason_code'), 'no_acceptable_official_source_found')

    def test_provider_candidate_urls_bypass_search_provider_and_use_mocked_fetch_only(self):
        calls = {'search_called': False, 'fetch_calls': []}

        def _search_provider(_q):
            calls['search_called'] = True
            raise AssertionError('search_provider should not be called when candidate_urls are supplied')

        def _fetch_provider(url, timeout):
            calls['fetch_calls'].append((url, timeout))
            return {
                'final_url': str(url),
                'title': 'UFC Test Card',
                'source_date': '2026-01-01',
                'html': '<html><body>Alpha defeated Beta by decision in round 3</body></html>',
            }

        provider = OfficialSourceLookupProvider(
            search_provider=_search_provider,
            fetch_provider=_fetch_provider,
            now_provider=lambda: datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
        result = provider.run_preview_lookup(
            selected_key='alpha|beta',
            selected_row={'fight_name': 'Alpha vs Beta'},
            candidate_urls=['https://ufc.com/event/test-card'],
        )
        self.assertFalse(calls['search_called'])
        self.assertEqual(calls['fetch_calls'], [('https://ufc.com/event/test-card', 6)])
        self.assertEqual(result.get('reason_code'), 'accepted_preview')
        self.assertTrue(result.get('external_lookup_performed'))
        self.assertTrue(result.get('candidate_urls_supplied'))
        self.assertEqual(result.get('candidate_url_count'), 1)

    def test_provider_candidate_urls_rejects_disallowed_without_fetch(self):
        calls = {'fetch_called': False}

        provider = OfficialSourceLookupProvider(
            search_provider=lambda _q: (_ for _ in ()).throw(AssertionError('search_provider should not run')),
            fetch_provider=lambda _url, _timeout: calls.__setitem__('fetch_called', True),
            now_provider=lambda: datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
        result = provider.run_preview_lookup(
            selected_key='alpha|beta',
            selected_row={'fight_name': 'Alpha vs Beta'},
            candidate_urls=['https://bad.example.com/result'],
        )
        self.assertFalse(calls['fetch_called'])
        self.assertEqual(result.get('reason_code'), 'source_url_not_allowed')
        self.assertTrue(result.get('candidate_urls_supplied'))
        self.assertEqual(result.get('candidate_url_count'), 1)

    def test_official_source_helpers_accept_official_https_allowlist_hosts(self):
        self.assertTrue(_is_allowed_official_source_url('https://ufc.com/event/test-card'))
        self.assertTrue(_is_allowed_official_source_url('https://results.ufc.com/event/test-card'))
        self.assertTrue(_is_allowed_official_source_url('https://tapology.com/fightcenter/events/test-card'))

    def test_official_source_helpers_reject_non_https(self):
        self.assertFalse(_is_allowed_official_source_url('http://ufc.com/event/test-card'))

    def test_official_source_helpers_reject_shorteners_and_opaque_wrappers(self):
        self.assertFalse(_is_allowed_official_source_url('https://bit.ly/test-card'))
        self.assertFalse(_is_allowed_official_source_url('https://t.co/test-card'))

    def test_official_source_host_classification_covers_all_tiers(self):
        self.assertEqual(_classify_official_source_host('https://ufc.com/event/test-card'), 'tier_a0')
        self.assertEqual(_classify_official_source_host('https://results.ufc.com/event/test-card'), 'tier_a1')
        self.assertEqual(_classify_official_source_host('https://tapology.com/fightcenter/events/test-card'), 'tier_b')

    def test_official_source_citation_incomplete_forces_manual_review(self):
        result = _validate_official_source_citation({
            'selected_key': 'alpha|beta',
            'source_url': 'https://ufc.com/event/test-card',
            'source_title': 'UFC Test Card',
            'publisher_host': 'ufc.com',
        })
        self.assertTrue(result.get('manual_review_required'))
        self.assertEqual(result.get('reason_code'), 'citation_incomplete')
        self.assertFalse(result.get('accepted_preview'))

    def test_official_source_confidence_thresholds_classify_accepted_manual_review_and_rejected(self):
        accepted = _classify_source_confidence({'source_url': 'https://ufc.com/event/test-card'})
        manual_review = _classify_source_confidence({'source_url': 'https://tapology.com/fightcenter/events/test-card'})
        rejected = _classify_source_confidence({'source_url': 'http://unknown.example/test-card'})
        self.assertEqual(accepted.get('classification'), 'accepted_preview')
        self.assertEqual(manual_review.get('classification'), 'manual_review')
        self.assertEqual(rejected.get('classification'), 'rejected_manual_review')

    def test_official_source_citation_fingerprint_is_stable_for_same_inputs(self):
        citation = {
            'source_url': 'https://ufc.com/event/test-card',
            'source_title': 'UFC Test Card',
            'source_date': '2026-01-01',
            'winner': 'Alpha',
            'method': 'Decision',
            'round_time': 'R3 5:00',
        }
        self.assertEqual(
            _build_citation_fingerprint('alpha|beta', citation),
            _build_citation_fingerprint('alpha|beta', citation),
        )

    def test_advanced_dashboard_has_official_source_preview_controls(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'operator-official-source-selected-key', resp.data)
        self.assertIn(b'operator-official-source-preview-btn', resp.data)
        self.assertIn(b'operator-official-source-preview-output', resp.data)
        self.assertIn(b'/api/operator/actual-result-lookup/official-source-one-record-preview', resp.data)

    def test_official_source_preview_not_called_on_page_load(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')
        dom_ready_start = page.find("window.addEventListener('DOMContentLoaded', () => {")
        self.assertNotEqual(dom_ready_start, -1)
        dom_ready_slice = page[dom_ready_start:dom_ready_start + 1300]
        self.assertNotIn('/api/operator/actual-result-lookup/official-source-one-record-preview', dom_ready_slice)

    def test_official_source_preview_ui_no_approval_granted_wired(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')
        # Confirm approval_granted: false is wired in the fetch body (not true)
        idx = page.find('official-source-one-record-preview')
        self.assertNotEqual(idx, -1)
        surrounding = page[idx:idx + 600]
        self.assertIn('approval_granted', surrounding)
        self.assertNotIn('approval_granted: true', surrounding)

    def test_advanced_dashboard_has_premium_report_factory_intake_panel(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Premium Report Factory - Event Card Intake Preview', resp.data)
        self.assertIn(b'operator-prf-preview-btn', resp.data)
        self.assertIn(b'Preview Event Card', resp.data)
        self.assertIn(b'/api/premium-report-factory/intake/preview', resp.data)

    def test_advanced_dashboard_premium_report_factory_intake_fields_and_outputs_exist(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)

        for required_id in (
            b'operator-prf-raw-card-text',
            b'operator-prf-event-name',
            b'operator-prf-event-date',
            b'operator-prf-promotion',
            b'operator-prf-location',
            b'operator-prf-source-reference',
            b'operator-prf-notes',
            b'operator-prf-event-preview-output',
            b'operator-prf-matchup-preview-output',
            b'operator-prf-parse-warnings-output',
            b'operator-prf-errors-output',
        ):
            self.assertIn(required_id, resp.data)

        for table_field in (
            b'temporary_matchup_id',
            b'fighter_a',
            b'fighter_b',
            b'bout_order',
            b'weight_class',
            b'ruleset',
            b'source_reference',
            b'parse_status',
            b'parse_notes',
        ):
            self.assertIn(table_field, resp.data)

    def test_premium_report_factory_intake_preview_not_called_on_page_load(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')
        dom_ready_start = page.find("window.addEventListener('DOMContentLoaded', () => {")
        self.assertNotEqual(dom_ready_start, -1)
        dom_ready_slice = page[dom_ready_start:dom_ready_start + 1300]
        self.assertNotIn('/api/premium-report-factory/intake/preview', dom_ready_slice)

    def test_premium_report_factory_intake_panel_has_no_write_controls(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')
        panel_start = page.find('Premium Report Factory - Event Card Intake Preview')
        self.assertNotEqual(panel_start, -1)
        panel_end = page.find('operator-dry-run-preview-btn', panel_start)
        self.assertNotEqual(panel_end, -1)
        panel_slice = page[panel_start:panel_end]

        self.assertNotIn('operator-prf-save-btn', panel_slice)
        self.assertNotIn('operator-prf-write-btn', panel_slice)
        self.assertNotIn('operator-prf-apply-btn', panel_slice)
        self.assertNotIn('operator-prf-report-btn', panel_slice)
        self.assertNotIn('operator-prf-result-btn', panel_slice)
        self.assertNotIn('operator-prf-learning-btn', panel_slice)

    def test_advanced_dashboard_has_guarded_single_lookup_controls(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'operator-guarded-selected-key', resp.data)
        self.assertIn(b'operator-guarded-approval-checkbox', resp.data)
        self.assertIn(b'operator-guarded-single-lookup-btn', resp.data)
        self.assertIn(b'operator-guarded-single-output', resp.data)
        self.assertIn(b'/api/operator/actual-result-lookup/guarded-single', resp.data)

    def test_advanced_guarded_single_not_called_on_page_load(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        page = resp.data.decode('utf-8', errors='ignore')

        dom_ready_start = page.find("window.addEventListener('DOMContentLoaded', () => {")
        self.assertNotEqual(dom_ready_start, -1)
        dom_ready_slice = page[dom_ready_start:dom_ready_start + 1300]
        self.assertNotIn('/api/operator/actual-result-lookup/guarded-single', dom_ready_slice)

    def test_manual_review_empty_state_message_present(self):
        expected = b'External result lookup is not connected for automatic queue resolution yet. Manual review required.'
        index_resp = self.client.get('/')
        self.assertEqual(index_resp.status_code, 200)
        self.assertIn(expected, index_resp.data)

        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        self.assertIn(expected, advanced_resp.data)

    def test_web_trigger_scout_panel_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Find Fight Results', resp.data)
        self.assertIn(b'/api/operator/web-trigger-scout', resp.data)

    def test_web_trigger_scout_endpoint_contract(self):
        resp = self.client.post(
            '/api/operator/web-trigger-scout',
            json={
                'query': 'check Jafel Filho vs Cody Durden result',
                'mode': 'official_first',
                'targets': [],
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('results', data)
        self.assertIn('blocked_actions', data)
        self.assertIsInstance(data.get('results'), list)
        self.assertIsInstance(data.get('blocked_actions'), list)
        if data['results']:
            row = data['results'][0]
            for key in (
                'trigger_type',
                'fighter_or_event_name',
                'result_found',
                'winner',
                'method',
                'round_time',
                'official_source_url',
                'source_confidence',
                'recommended_action',
            ):
                self.assertIn(key, row)

    def test_signal_breakdown_contract(self):
        resp = self.client.get('/api/accuracy/signal-breakdown')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('breakdown', data)
        self.assertIn('has_data', data)
        self.assertIsInstance(data.get('breakdown'), list)
        buckets = [b['bucket'] for b in data['breakdown']]
        self.assertIn('0.00–0.10', buckets)
        self.assertIn('0.11–0.20', buckets)
        self.assertIn('0.21–0.30', buckets)
        self.assertIn('0.31+', buckets)

    def test_signal_breakdown_panel_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/signal-breakdown', resp.data)

    def test_method_round_breakdown_contract(self):
        resp = self.client.get('/api/accuracy/method-round-breakdown')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('has_data', data)
        self.assertIn('method_accuracy', data)
        self.assertIn('round_accuracy', data)
        self.assertIn('stoppage_propensity_buckets', data)
        self.assertIn('round_finish_tendency_buckets', data)
        m = data['method_accuracy']
        for key in ('total_available', 'method_hits', 'method_misses', 'method_accuracy_pct'):
            self.assertIn(key, m)
        r = data['round_accuracy']
        for key in ('total_available', 'round_hits', 'round_misses', 'round_accuracy_pct'):
            self.assertIn(key, r)
        # Each propensity list should have 4 buckets
        self.assertEqual(len(data['stoppage_propensity_buckets']), 4)
        self.assertEqual(len(data['round_finish_tendency_buckets']), 4)
        buckets = [b['bucket'] for b in data['stoppage_propensity_buckets']]
        for expected in ('0.00–0.25', '0.26–0.50', '0.51–0.75', '0.76–1.00'):
            self.assertIn(expected, buckets)

    def test_method_round_panels_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/method-round-breakdown', resp.data)

    def test_confidence_calibration_contract(self):
        resp = self.client.get('/api/accuracy/confidence-calibration')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('has_data', data)
        self.assertIn('calibration', data)
        self.assertIsInstance(data['calibration'], list)
        self.assertEqual(len(data['calibration']), 5)
        buckets = [b['bucket'] for b in data['calibration']]
        for expected in ('0.50–0.60', '0.61–0.70', '0.71–0.80', '0.81–0.90', '0.91–1.00'):
            self.assertIn(expected, buckets)
        for b in data['calibration']:
            for key in ('total_compared', 'predicted_confidence_avg', 'actual_win_rate', 'calibration_gap'):
                self.assertIn(key, b)

    def test_confidence_calibration_panel_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/confidence-calibration', resp.data)

    def test_error_patterns_contract(self):
        resp = self.client.get('/api/accuracy/error-patterns')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('has_data', data)
        self.assertIn('total_misses', data)
        self.assertIn('top_failure_patterns', data)
        self.assertIn('miss_breakdowns', data)
        bd = data['miss_breakdowns']
        for key in ('by_signal_gap', 'by_confidence', 'by_method', 'by_round_range'):
            self.assertIn(key, bd)
            self.assertIsInstance(bd[key], list)
        self.assertIsInstance(data['top_failure_patterns'], list)
        self.assertIsInstance(data['total_misses'], int)

    def test_failure_patterns_panel_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/error-patterns', resp.data)

    def test_signal_coverage_contract(self):
        resp = self.client.get('/api/accuracy/signal-coverage')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('coverage', data)
        cov = data['coverage']
        for bucket in ('overall', 'resolved', 'unresolved'):
            self.assertIn(bucket, cov)
            b = cov[bucket]
            self.assertIn('total_predictions', b)
            for field in ('signal_gap_coverage_pct', 'stoppage_propensity_coverage_pct',
                          'round_finish_tendency_coverage_pct', 'predicted_method_coverage_pct',
                          'predicted_round_coverage_pct'):
                self.assertIn(field, b)

    def test_signal_coverage_panel_present(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/signal-coverage', resp.data)

    def test_structural_signal_backfill_planner_contract(self):
        resp = self.client.get('/api/accuracy/structural-signal-backfill-planner')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('planner', data)
        planner = data['planner']
        for key in ('total_predictions', 'predictions_needing_backfill', 'structural_fields', 'summary', 'priority_queue'):
            self.assertIn(key, planner)
        summary = planner['summary']
        for key in ('unresolved_needing_backfill', 'resolved_needing_backfill', 'resolved_miss_needing_backfill'):
            self.assertIn(key, summary)
        # backwards-compat: eligibility_counts must now also be present
        self.assertIn('eligibility_counts', summary)
        self.assertIsInstance(planner['priority_queue'], list)
        if planner['priority_queue']:
            row = planner['priority_queue'][0]
            for key in ('fight_id', 'missing_signals', 'missing_count', 'priority_score', 'priority_tier'):
                self.assertIn(key, row)

    def test_planner_queue_rows_have_eligibility_fields(self):
        """Every queue entry must carry all four eligibility fields."""
        resp = self.client.get('/api/accuracy/structural-signal-backfill-planner')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        queue = data['planner']['priority_queue']
        for row in queue:
            for key in ('eligibility_class', 'eligibility_reason', 'source_value_status',
                        'source_values_found', 'recommended_action'):
                self.assertIn(key, row, f"Missing key '{key}' in queue row for {row.get('fight_id')}")

    def test_planner_eligibility_counts_keys_present(self):
        """Summary must contain all four eligibility class counters."""
        resp = self.client.get('/api/accuracy/structural-signal-backfill-planner')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        ec = data['planner']['summary']['eligibility_counts']
        for cls in ('READY_FOR_BACKFILL', 'BLOCKED_NEEDS_SOURCE_VALUES',
                    'REQUIRES_ENGINE_RERUN', 'UNRESOLVED_RESULT_PENDING'):
            self.assertIn(cls, ec)

    def test_structural_signal_backfill_planner_panel_present(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'/api/accuracy/structural-signal-backfill-planner', resp.data)


    # â”€â”€ batch/guarded-local-apply tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    APPLY_URL = '/api/operator/actual-result-lookup/batch/guarded-local-apply'

    def _valid_apply_token(self, selected_keys):
        token, _ = _build_batch_preview_execution_token(selected_keys)
        return token

    def _expired_apply_token(self, selected_keys):
        digest = _build_selected_keys_digest(selected_keys)
        return f"batch_preview_{int(time()) - 400}_{digest}_{uuid.uuid4().hex}"

    def _future_apply_token(self, selected_keys):
        digest = _build_selected_keys_digest(selected_keys)
        return f"batch_preview_{int(time()) + 400}_{digest}_{uuid.uuid4().hex}"

    # Test 1: rejects approval_granted=false
    def test_batch_local_apply_rejects_approval_false(self):
        token = self._valid_apply_token(['k1'])
        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': False,
            'selected_keys': ['k1'],
            'execution_token': token,
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertFalse(data.get('scoring_semantics_changed'))

    # Test 2: rejects missing execution_token
    def test_batch_local_apply_rejects_missing_token(self):
        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': True,
            'selected_keys': ['k1'],
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('execution_token', (data.get('error') or '').lower())
        self.assertFalse(data.get('mutation_performed'))

    # Test 3: rejects malformed token
    def test_batch_local_apply_rejects_malformed_token(self):
        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': True,
            'selected_keys': ['k1'],
            'execution_token': 'garbage_not_valid',
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('mutation_performed'))
        self.assertIn('format invalid', (data.get('error') or '').lower())

    # Test 4: rejects expired token
    def test_batch_local_apply_rejects_expired_token(self):
        token = self._expired_apply_token(['k1'])
        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': True,
            'selected_keys': ['k1'],
            'execution_token': token,
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('expired', (data.get('error') or '').lower())
        self.assertFalse(data.get('mutation_performed'))

    # Test 5: rejects future-issued token
    def test_batch_local_apply_rejects_future_token(self):
        token = self._future_apply_token(['k1'])
        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': True,
            'selected_keys': ['k1'],
            'execution_token': token,
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('invalid', (data.get('error') or '').lower())
        self.assertFalse(data.get('mutation_performed'))

    # Test 6: rejects selected_keys digest mismatch
    def test_batch_local_apply_rejects_digest_mismatch(self):
        # Token was issued for ['k1'], but apply submits ['k2']
        token = self._valid_apply_token(['k1'])
        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': True,
            'selected_keys': ['k2'],
            'execution_token': token,
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('mismatch', (data.get('error') or '').lower())
        self.assertFalse(data.get('mutation_performed'))

    # Test 7: rejects empty selected_keys
    def test_batch_local_apply_rejects_empty_selected_keys(self):
        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': True,
            'selected_keys': [],
            'execution_token': 'some_nonempty_token',
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('selected_keys', (data.get('error') or '').lower())
        self.assertFalse(data.get('mutation_performed'))

    # Test 8: rejects duplicate selected_keys
    def test_batch_local_apply_rejects_duplicate_selected_keys(self):
        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': True,
            'selected_keys': ['k1', 'k1'],
            'execution_token': 'some_nonempty_token',
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('duplicates', (data.get('error') or '').lower())
        self.assertFalse(data.get('mutation_performed'))

    # Test 9: rejects over hard cap
    def test_batch_local_apply_rejects_over_hard_cap(self):
        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': True,
            'selected_keys': ['k1', 'k2', 'k3', 'k4', 'k5', 'k6'],
            'execution_token': 'some_nonempty_token',
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn('hard cap', (data.get('error') or '').lower())
        self.assertFalse(data.get('mutation_performed'))

    # Test 10: valid token + no local result â†’ no mutation, real files unchanged
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_batch_local_apply_valid_token_no_local_result_no_mutation(self, mock_summary, mock_local_map):
        selected_key = 'ghost_fight|predictions_ghost_fight_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Ghost Fight',
                'predicted_winner': 'fighter_a',
                'event_date': '2026-01-01',
                'file_path': 'predictions/ghost_fight.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        root = Path(__file__).resolve().parent.parent
        mock_local_map.return_value = ({}, root / 'ops' / 'accuracy')
        token = self._valid_apply_token([selected_key])
        before = self._actual_results_file_hashes()

        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': True,
            'selected_keys': [selected_key],
            'execution_token': token,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('total_written'), 0)
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertFalse(data.get('scoring_semantics_changed'))
        self.assertFalse(data.get('partial_rollback_performed'))
        after = self._actual_results_file_hashes()
        self.assertEqual(before, after)

    # Test 11: valid token + local result found â†’ writes exactly one row to manual file only
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_batch_local_apply_valid_token_writes_one_row_to_manual_only(self, mock_summary, mock_local_map):
        selected_key = 'alpha_vs_beta|predictions_alpha_vs_beta_prediction_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Alpha vs Beta',
                'predicted_winner': 'Alpha',
                'event_date': '2026-01-01',
                'file_path': 'predictions/alpha_vs_beta_prediction.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            accuracy_dir = Path(tmp) / 'ops' / 'accuracy'
            accuracy_dir.mkdir(parents=True, exist_ok=True)
            manual_path = accuracy_dir / 'actual_results_manual.json'
            manual_path.write_text('[]\n', encoding='utf-8')
            (accuracy_dir / 'actual_results.json').write_text('[]\n', encoding='utf-8')
            (accuracy_dir / 'actual_results_unresolved.json').write_text('[]\n', encoding='utf-8')

            mock_local_map.return_value = ({
                'alpha_vs_beta': {
                    'record': {
                        'fight_id': 'alpha_vs_beta',
                        'actual_winner': 'alpha',
                        'actual_method': 'Decision',
                        'actual_round': '3',
                        'event_date': '2026-01-01',
                        'source': 'manual',
                    },
                    'source_file': 'actual_results_manual.json',
                }
            }, accuracy_dir)

            token = self._valid_apply_token([selected_key])
            before_repo = self._actual_results_file_hashes()

            resp = self.client.post(self.APPLY_URL, json={
                'mode': 'local_only',
                'approval_granted': True,
                'selected_keys': [selected_key],
                'execution_token': token,
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data.get('ok'))
            self.assertEqual(data.get('total_written'), 1)
            self.assertEqual(data.get('total_skipped'), 0)
            self.assertTrue(data.get('mutation_performed'))
            self.assertFalse(data.get('external_lookup_performed'))
            self.assertFalse(data.get('bulk_lookup_performed'))
            self.assertFalse(data.get('scoring_semantics_changed'))
            self.assertFalse(data.get('partial_rollback_performed'))
            self.assertEqual(data.get('mode'), 'batch_local_apply')

            rows = data.get('rows') or []
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertTrue(row.get('write_performed'))
            self.assertEqual(row.get('reason_code'), 'local_result_applied')
            self.assertEqual(row.get('proposed_write', {}).get('source'), 'guarded_batch_local_apply')

            written = json.loads(manual_path.read_text(encoding='utf-8'))
            matched = [r for r in written if r.get('fight_id') == 'alpha_vs_beta']
            self.assertEqual(len(matched), 1)

            # Real repo files untouched
            after_repo = self._actual_results_file_hashes()
            self.assertEqual(before_repo, after_repo)

    # Test 12: actual_results.json and actual_results_unresolved.json never written
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_batch_local_apply_no_writes_to_non_manual_files(self, mock_summary, mock_local_map):
        selected_key = 'bravo_vs_charlie|predictions_bravo_vs_charlie_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Bravo vs Charlie',
                'predicted_winner': 'Bravo',
                'event_date': '2026-02-01',
                'file_path': 'predictions/bravo_vs_charlie.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            accuracy_dir = Path(tmp) / 'ops' / 'accuracy'
            accuracy_dir.mkdir(parents=True, exist_ok=True)
            (accuracy_dir / 'actual_results_manual.json').write_text('[]\n', encoding='utf-8')
            ar_path = accuracy_dir / 'actual_results.json'
            ur_path = accuracy_dir / 'actual_results_unresolved.json'
            ar_path.write_text('[]\n', encoding='utf-8')
            ur_path.write_text('[]\n', encoding='utf-8')
            hash_ar_before = hashlib.sha256(ar_path.read_bytes()).hexdigest()
            hash_ur_before = hashlib.sha256(ur_path.read_bytes()).hexdigest()

            mock_local_map.return_value = ({
                'bravo_vs_charlie': {
                    'record': {
                        'fight_id': 'bravo_vs_charlie',
                        'actual_winner': 'bravo',
                        'actual_method': 'KO',
                        'actual_round': '1',
                        'event_date': '2026-02-01',
                        'source': 'manual',
                    },
                    'source_file': 'actual_results_manual.json',
                }
            }, accuracy_dir)

            token = self._valid_apply_token([selected_key])
            self.client.post(self.APPLY_URL, json={
                'mode': 'local_only',
                'approval_granted': True,
                'selected_keys': [selected_key],
                'execution_token': token,
            })
            self.assertEqual(hashlib.sha256(ar_path.read_bytes()).hexdigest(), hash_ar_before)
            self.assertEqual(hashlib.sha256(ur_path.read_bytes()).hexdigest(), hash_ur_before)

    # Test 13: rollback restores manual file when write fails mid-batch
    @patch('app._upsert_single_manual_actual_result')
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_batch_local_apply_rollback_on_write_failure(self, mock_summary, mock_local_map, mock_upsert):
        selected_key = 'delta_vs_echo|predictions_delta_vs_echo_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [{
                'fight_name': 'Delta vs Echo',
                'predicted_winner': 'Delta',
                'event_date': '2026-03-01',
                'file_path': 'predictions/delta_vs_echo.json',
                'status': 'waiting_for_actual_result',
            }],
            'compared_results': [],
            'summary_metrics': {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            accuracy_dir = Path(tmp) / 'ops' / 'accuracy'
            accuracy_dir.mkdir(parents=True, exist_ok=True)
            manual_path = accuracy_dir / 'actual_results_manual.json'
            original_bytes = b'[]\n'
            manual_path.write_bytes(original_bytes)

            mock_local_map.return_value = ({
                'delta_vs_echo': {
                    'record': {
                        'fight_id': 'delta_vs_echo',
                        'actual_winner': 'delta',
                        'actual_method': 'TKO',
                        'actual_round': '2',
                        'event_date': '2026-03-01',
                        'source': 'manual',
                    },
                    'source_file': 'actual_results_manual.json',
                }
            }, accuracy_dir)

            def corrupt_then_fail(acc_dir, write_row):
                (acc_dir / 'actual_results_manual.json').write_text(
                    '[{"corrupt": "partial_write"}]\n', encoding='utf-8'
                )
                return {
                    'ok': False,
                    'before_row_count': 0,
                    'after_row_count': 0,
                    'write_target': str(acc_dir / 'actual_results_manual.json'),
                }
            mock_upsert.side_effect = corrupt_then_fail

            token = self._valid_apply_token([selected_key])
            resp = self.client.post(self.APPLY_URL, json={
                'mode': 'local_only',
                'approval_granted': True,
                'selected_keys': [selected_key],
                'execution_token': token,
            })
            self.assertEqual(resp.status_code, 500)
            data = resp.get_json()
            self.assertFalse(data.get('ok'))
            self.assertTrue(data.get('partial_rollback_performed'))
            self.assertEqual(data.get('total_written'), 0)
            self.assertFalse(data.get('mutation_performed'))
            # Rollback must have restored the original content
            self.assertEqual(manual_path.read_bytes(), original_bytes)

    # Test 14: verify new preview token format (5 parts, digest bound to keys)
    def test_batch_local_preview_token_format_includes_keys_digest(self):
        selected_keys = ['k1', 'k2']
        token, _ = _build_batch_preview_execution_token(selected_keys)
        parts = token.split('_')
        self.assertEqual(len(parts), 5)
        self.assertEqual(parts[0], 'batch')
        self.assertEqual(parts[1], 'preview')
        digest_in_token = parts[3]
        expected_digest = _build_selected_keys_digest(selected_keys)
        self.assertEqual(digest_in_token, expected_digest)

    # Test 15: apply rejects mode != local_only with all guardrail flags false
    def test_batch_local_apply_rejects_mode_not_local_only(self):
        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'web',
            'approval_granted': True,
            'selected_keys': ['k1'],
            'execution_token': 'some_token',
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('mutation_performed'))
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertFalse(data.get('bulk_lookup_performed'))
        self.assertFalse(data.get('scoring_semantics_changed'))

    # Test 16: success response contains all required top-level fields
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_batch_local_apply_success_response_has_required_fields(self, mock_summary, mock_local_map):
        selected_key = 'foxtrot_vs_golf|predictions_foxtrot_vs_golf_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [],
            'compared_results': [],
            'summary_metrics': {},
        }
        root = Path(__file__).resolve().parent.parent
        mock_local_map.return_value = ({}, root / 'ops' / 'accuracy')
        token = self._valid_apply_token([selected_key])

        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': True,
            'selected_keys': [selected_key],
            'execution_token': token,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        for field in (
            'ok', 'mode', 'batch_size_requested', 'batch_size_accepted', 'hard_cap',
            'total_written', 'total_skipped', 'mutation_performed',
            'external_lookup_performed', 'bulk_lookup_performed',
            'scoring_semantics_changed', 'partial_rollback_performed',
            'execution_token_used', 'token_age_seconds', 'selected_keys_digest', 'rows',
        ):
            self.assertIn(field, data, f"Missing required field: {field}")
        self.assertEqual(data.get('mode'), 'batch_local_apply')
        self.assertEqual(data.get('hard_cap'), 5)
        self.assertIsInstance(data.get('rows'), list)

    # Test 17: each row in response contains all required per-row audit fields
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_batch_local_apply_per_row_audit_fields_present(self, mock_summary, mock_local_map):
        selected_key = 'hotel_vs_india|predictions_hotel_vs_india_json'
        mock_summary.return_value = {
            'ok': True,
            'waiting_for_results': [],
            'compared_results': [],
            'summary_metrics': {},
        }
        root = Path(__file__).resolve().parent.parent
        mock_local_map.return_value = ({}, root / 'ops' / 'accuracy')
        token = self._valid_apply_token([selected_key])

        resp = self.client.post(self.APPLY_URL, json={
            'mode': 'local_only',
            'approval_granted': True,
            'selected_keys': [selected_key],
            'execution_token': token,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        rows = data.get('rows') or []
        self.assertEqual(len(rows), 1)
        row = rows[0]
        for field in (
            'selected_key', 'row_found', 'local_result_found', 'write_performed',
            'proposed_write', 'write_target', 'before_row_count', 'after_row_count',
            'reason_code',
        ):
            self.assertIn(field, row, f"Missing per-row field: {field}")

    # Test 18: preview response now includes selected_keys_digest bound to the submitted keys
    def test_batch_local_preview_response_includes_selected_keys_digest(self):
        resp = self.client.post(
            '/api/operator/actual-result-lookup/batch/guarded-local-preview',
            json={
                'mode': 'local_only',
                'approval_granted': False,
                'selected_keys': ['k1', 'k2'],
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('selected_keys_digest', data)
        self.assertIsNotNone(data.get('selected_keys_digest'))
        expected = _build_selected_keys_digest(['k1', 'k2'])
        self.assertEqual(data.get('selected_keys_digest'), expected)

    # --- UI Template Tests for Batch Local Apply ---

    def test_index_html_contains_batch_preview_section(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('Controlled Batch Local Apply', html)
        self.assertIn('batch-selected-keys-input', html)
        self.assertIn('batch-preview-btn', html)

    def test_index_html_contains_batch_apply_button(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('batch-apply-btn', html)
        self.assertIn('Apply Changes', html)

    def test_index_html_contains_batch_approval_checkbox(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('batch-approval-checkbox', html)
        self.assertIn('I approve applying this exact previewed selected-key batch', html)

    def test_index_html_contains_batch_safety_messages(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        # Safety message requirements
        self.assertIn('Local-only apply', html)
        self.assertIn('No web lookup', html)
        self.assertIn('No scoring semantics change', html)
        self.assertIn('Maximum 5 selected rows', html)
        self.assertIn('Fresh token', html)
        self.assertIn('explicit approval required', html)

    def test_index_html_batch_endpoint_references(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        # Check for endpoint URLs in JavaScript
        self.assertIn('/api/operator/actual-result-lookup/batch/guarded-local-preview', html)
        self.assertIn('/api/operator/actual-result-lookup/batch/guarded-local-apply', html)

    def test_index_html_batch_result_display_fields(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        # Preview result fields
        self.assertIn('batch-size-requested', html)
        self.assertIn('batch-size-accepted', html)
        self.assertIn('batch-hard-cap', html)
        self.assertIn('batch-token-ttl', html)
        self.assertIn('batch-execution-token', html)
        self.assertIn('batch-token-digest', html)
        self.assertIn('batch-preview-rows', html)
        self.assertIn('batch-preview-status', html)
        # Apply result fields
        self.assertIn('batch-total-written', html)
        self.assertIn('batch-total-skipped', html)
        self.assertIn('batch-mutation-performed', html)
        self.assertIn('batch-partial-rollback', html)
        self.assertIn('batch-external-lookup-performed', html)
        self.assertIn('batch-bulk-lookup-performed', html)
        self.assertIn('batch-scoring-semantics-changed', html)
        self.assertIn('batch-apply-rows', html)
        self.assertIn('batch-apply-status', html)

    def test_index_html_no_auto_batch_calls_on_page_load(self):
        """Verify DOMContentLoaded does not invoke batch endpoints."""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        # DOMContentLoaded should only call accuracy and health
        # Check that batch calls are NOT in the DOMContentLoaded block
        lines = html.split('\n')
        dom_content_start = None
        dom_content_end = None
        for i, line in enumerate(lines):
            if "DOMContentLoaded" in line:
                dom_content_start = i
            if dom_content_start is not None and ('});' in line or '</script>' in line):
                dom_content_end = i
                break
        
        self.assertIsNotNone(dom_content_start, "DOMContentLoaded block not found")
        dom_block = '\n'.join(lines[dom_content_start:dom_content_end + 1])
        # These calls should NOT be in DOMContentLoaded
        self.assertNotIn('guarded-local-preview', dom_block, 
                        "batch preview should not be called on DOMContentLoaded")
        self.assertNotIn('guarded-local-apply', dom_block,
                        "batch apply should not be called on DOMContentLoaded")

    def test_operator_run_calibration_review_route_still_works(self):
        mock_result = {
            'timestamp': '2026-05-01T00:00:00Z',
            'fights_analyzed': 3,
            'miss_patterns': {'winner': 1},
            'proposed_calibrations': [{'field': 'confidence'}],
            'backtest_summary': {'total': 3},
            'confidence_in_calibration': 0.66,
            'recommendation': 'keep current threshold',
        }

        with patch.object(app_module, 'MatchupOperator') as mock_operator_cls:
            mock_operator_cls.return_value.run_calibration_review.return_value = mock_result
            resp = self.client.post('/api/operator/run-calibration-review', json={})

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertTrue(data.get('approval_required'))
        self.assertEqual(data.get('fights_analyzed'), 3)
        self.assertIn('recommendation', data)

    def test_operator_accuracy_calibration_review_alias_matches_canonical_shape(self):
        mock_result = {
            'timestamp': '2026-05-01T00:00:00Z',
            'fights_analyzed': 5,
            'miss_patterns': {'method': 2},
            'proposed_calibrations': [{'field': 'method'}],
            'backtest_summary': {'total': 5},
            'confidence_in_calibration': 0.72,
            'recommendation': 'review method weighting',
        }

        with patch.object(app_module, 'MatchupOperator') as mock_operator_cls:
            mock_operator_cls.return_value.run_calibration_review.return_value = mock_result
            canonical_resp = self.client.post('/api/operator/run-calibration-review', json={})

        with patch.object(app_module, 'MatchupOperator') as mock_operator_cls:
            mock_operator_cls.return_value.run_calibration_review.return_value = mock_result
            alias_resp = self.client.post('/api/operator/accuracy-calibration-review', json={})

        self.assertEqual(canonical_resp.status_code, 200)
        self.assertEqual(alias_resp.status_code, 200)

        canonical_data = canonical_resp.get_json()
        alias_data = alias_resp.get_json()

        self.assertEqual(set(alias_data.keys()), set(canonical_data.keys()))
        for key in ('ok', 'approval_required', 'fights_analyzed', 'confidence_in_calibration'):
            self.assertEqual(alias_data.get(key), canonical_data.get(key))

        self.assertNotEqual(alias_data, {'error': 'Operator endpoint not found', 'ok': False})

    def test_premium_report_factory_phase1_intake_preview_clean_card_contract(self):
        payload = {
            'raw_card_text': 'Alpha vs Beta\nGamma v Delta',
            'event_name': 'Test Card',
            'event_date': '2026-05-10',
            'promotion': 'AI-RISA FC',
            'location': 'London',
            'source_reference': 'manual_operator_entry',
            'notes': 'phase1 smoke',
        }

        resp = self.client.post('/api/premium-report-factory/intake/preview', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()

        for field in ('ok', 'generated_at', 'event_preview', 'matchup_previews', 'parse_warnings', 'errors'):
            self.assertIn(field, data)
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('parse_warnings'), [])
        self.assertEqual(data.get('errors'), [])

        event_preview = data.get('event_preview') or {}
        self.assertEqual(event_preview.get('event_name'), payload['event_name'])
        self.assertEqual(event_preview.get('event_date'), payload['event_date'])
        self.assertEqual(event_preview.get('promotion'), payload['promotion'])
        self.assertEqual(event_preview.get('location'), payload['location'])
        self.assertEqual(event_preview.get('source_reference'), payload['source_reference'])
        self.assertEqual(event_preview.get('notes'), payload['notes'])
        self.assertEqual(event_preview.get('raw_card_text_preserved'), payload['raw_card_text'])

        matchup_previews = data.get('matchup_previews') or []
        self.assertEqual(len(matchup_previews), 2)
        first = matchup_previews[0]
        for field in (
            'temporary_matchup_id', 'fighter_a', 'fighter_b', 'bout_order',
            'weight_class', 'ruleset', 'source_reference', 'parse_status', 'parse_notes',
        ):
            self.assertIn(field, first)
        self.assertEqual(first.get('fighter_a'), 'Alpha')
        self.assertEqual(first.get('fighter_b'), 'Beta')
        self.assertEqual(first.get('parse_status'), 'parsed')
        self.assertEqual(first.get('source_reference'), payload['source_reference'])

    def test_premium_report_factory_phase1_intake_preview_incomplete_row_needs_review(self):
        payload = {
            'raw_card_text': 'Alpha vs\nvs Beta',
            'event_name': 'Test Card',
            'event_date': '2026-05-10',
            'source_reference': 'manual_operator_entry',
        }
        resp = self.client.post('/api/premium-report-factory/intake/preview', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()

        previews = data.get('matchup_previews') or []
        self.assertGreaterEqual(len(previews), 2)
        self.assertEqual(previews[0].get('parse_status'), 'needs_review')
        self.assertEqual(previews[1].get('parse_status'), 'needs_review')

    def test_premium_report_factory_phase1_intake_preview_duplicate_lines_deterministic(self):
        payload = {
            'raw_card_text': 'Alpha vs Beta\nAlpha vs Beta\nAlpha vs Beta',
            'event_name': 'Determinism Card',
            'event_date': '2026-06-01',
            'source_reference': 'manual_operator_entry',
        }

        resp_one = self.client.post('/api/premium-report-factory/intake/preview', json=payload)
        resp_two = self.client.post('/api/premium-report-factory/intake/preview', json=payload)
        self.assertEqual(resp_one.status_code, 200)
        self.assertEqual(resp_two.status_code, 200)

        rows_one = (resp_one.get_json() or {}).get('matchup_previews') or []
        rows_two = (resp_two.get_json() or {}).get('matchup_previews') or []
        self.assertEqual(rows_one, rows_two)
        self.assertEqual(len(rows_one), 3)

    def test_premium_report_factory_phase1_intake_preview_missing_event_date_warns_not_fails(self):
        payload = {
            'raw_card_text': 'Alpha vs Beta',
            'event_name': 'No Date Card',
            'event_date': '',
            'source_reference': 'manual_operator_entry',
        }
        resp = self.client.post('/api/premium-report-factory/intake/preview', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('missing_event_date', data.get('parse_warnings') or [])
        self.assertEqual(data.get('errors'), [])

    def test_premium_report_factory_phase1_intake_preview_preserves_source_reference_and_raw_text(self):
        payload = {
            'raw_card_text': 'Alpha vs Beta\nGamma vs Delta\n',
            'event_name': 'Source Ref Card',
            'event_date': '2026-07-01',
            'source_reference': 'ops_sheet_2026_07_01',
        }
        resp = self.client.post('/api/premium-report-factory/intake/preview', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()

        event_preview = data.get('event_preview') or {}
        self.assertEqual(event_preview.get('source_reference'), payload['source_reference'])
        self.assertEqual(event_preview.get('raw_card_text_preserved'), payload['raw_card_text'])
        for row in data.get('matchup_previews') or []:
            self.assertEqual(row.get('source_reference'), payload['source_reference'])

    def test_premium_report_factory_phase1_intake_preview_has_no_storage_side_effects(self):
        before = self._actual_results_file_hashes()
        resp = self.client.post('/api/premium-report-factory/intake/preview', json={
            'raw_card_text': 'Alpha vs Beta',
            'event_name': 'No Write Card',
            'event_date': '2026-08-01',
            'source_reference': 'manual_operator_entry',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue((resp.get_json() or {}).get('ok'))
        after = self._actual_results_file_hashes()
        self.assertEqual(before, after)


    # -------------------------------------------------------------------------
    # Report-scoring bridge v2 endpoint tests
    # -------------------------------------------------------------------------

    def _write_bridge_v2_fixtures(
        self,
        temp_accuracy_dir,
        ledger_path,
        prediction_records,
        actual_records=None,
        ledger_rows=None,
    ):
        """Write fixture data for bridge v2 endpoint tests."""
        import json as _json
        from pathlib import Path as _Path
        _acc = _Path(temp_accuracy_dir)
        _acc.mkdir(parents=True, exist_ok=True)
        (_acc / 'accuracy_ledger.json').write_text(
            _json.dumps(prediction_records), encoding='utf-8'
        )
        if actual_records is not None:
            (_acc / 'actual_results.json').write_text(
                _json.dumps(actual_records), encoding='utf-8'
            )
        if ledger_rows is not None:
            _Path(ledger_path).write_text(
                ''.join(_json.dumps(r) + '\n' for r in ledger_rows),
                encoding='utf-8',
            )

    def test_bridge_v2_endpoint_safe_empty_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            ledger_path = temp_root / 'bridge_v2_ledger.jsonl'

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)

            self._write_bridge_v2_fixtures(temp_accuracy_dir, ledger_path, prediction_records=[], actual_records=[], ledger_rows=[])

            resp = self.client.get('/api/operator/report-scoring-bridge/summary')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            for key in ('ok', 'generated_at', 'bridge_available', 'total_records', 'latest_records', 'status_counts', 'errors'):
                self.assertIn(key, data)
            self.assertTrue(data['ok'])
            self.assertFalse(data['bridge_available'])
            self.assertEqual(data['total_records'], 0)
            self.assertEqual(data['latest_records'], [])
            for sk in ('ok', 'unresolved', 'conflict', 'missing'):
                self.assertEqual(data['status_counts'].get(sk), 0)
            self.assertEqual(data['errors'], [])

    def test_bridge_v2_endpoint_clean_scored_record_visible(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            ledger_path = temp_root / 'bridge_v2_ledger.jsonl'

            prediction_records = [{
                'prediction_report_id': 'rpt_clean_1',
                'fight_id': 'alpha_vs_beta',
                'predicted_winner_id': 'Alpha',
                'predicted_method': 'Decision',
                'predicted_round': 'R3',
                'confidence': 0.82,
            }]
            actual_records = [{
                'fight_id': 'alpha_vs_beta',
                'actual_winner': 'Alpha',
                'actual_method': 'Decision',
                'actual_round': 'R3',
            }]
            ledger_rows = [{
                'global_ledger_record_id': 'glr_clean_1',
                'local_result_key': 'alpha_vs_beta',
                'official_source_reference': {'source_url': 'https://ufc.com/event/test-card'},
                'approved_actual_result': {
                    'fight_id': 'alpha_vs_beta',
                    'actual_winner': 'Alpha',
                    'actual_method': 'Decision',
                    'actual_round': 'R3',
                },
            }]

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)
            self._write_bridge_v2_fixtures(temp_accuracy_dir, ledger_path, prediction_records, actual_records, ledger_rows)

            resp = self.client.get('/api/operator/report-scoring-bridge/summary')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self.assertTrue(data['ok'])
            self.assertTrue(data['bridge_available'])
            self.assertEqual(data['total_records'], 1)
            record = data['latest_records'][0]
            self.assertEqual(record['prediction_report_id'], 'rpt_clean_1')
            self.assertTrue(record['scored'])
            self.assertEqual(record['scoring_bridge_status'], 'ok')
            self.assertIn(record['score_outcome'], ('round_exact', 'method_correct', 'winner_correct'))
            self.assertIn('generated_at', record)

    def test_bridge_v2_endpoint_unresolved_record_visible(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            ledger_path = temp_root / 'bridge_v2_ledger.jsonl'

            prediction_records = [{
                'prediction_report_id': 'rpt_unresolved_1',
                'fight_id': 'gamma_vs_delta',
                'predicted_winner_id': 'Gamma',
                'predicted_method': 'KO',
                'predicted_round': 'R1',
                'confidence': 0.65,
            }]

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)
            self._write_bridge_v2_fixtures(temp_accuracy_dir, ledger_path, prediction_records, actual_records=[], ledger_rows=[])

            resp = self.client.get('/api/operator/report-scoring-bridge/summary')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self.assertTrue(data['ok'])
            self.assertTrue(data['bridge_available'])
            record = data['latest_records'][0]
            self.assertFalse(record['scored'])
            self.assertEqual(record['score_outcome'], 'unresolved')
            self.assertEqual(record['scoring_bridge_status'], 'unresolved')

    def test_bridge_v2_endpoint_mismatch_visible(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            ledger_path = temp_root / 'bridge_v2_ledger.jsonl'

            prediction_records = [{
                'prediction_report_id': 'rpt_mismatch_1',
                'fight_id': 'eta_vs_zeta',
                'predicted_winner_id': 'Eta',
                'predicted_method': 'KO',
                'predicted_round': 'R1',
                'confidence': 0.70,
            }]
            actual_records = [{
                'fight_id': 'eta_vs_zeta',
                'actual_winner': 'Zeta',
                'actual_method': 'Decision',
                'actual_round': 'R3',
            }]
            ledger_rows = [{
                'global_ledger_record_id': 'glr_mismatch_1',
                'local_result_key': 'eta_vs_zeta',
                'official_source_reference': {'source_url': 'https://ufc.com/event/test-card'},
                'approved_actual_result': {
                    'fight_id': 'eta_vs_zeta',
                    'actual_winner': 'Zeta',
                    'actual_method': 'Decision',
                    'actual_round': 'R3',
                },
            }]

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)
            self._write_bridge_v2_fixtures(temp_accuracy_dir, ledger_path, prediction_records, actual_records, ledger_rows)

            resp = self.client.get('/api/operator/report-scoring-bridge/summary')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self.assertTrue(data['ok'])
            record = data['latest_records'][0]
            self.assertTrue(record['scored'])
            self.assertEqual(record['score_outcome'], 'mismatch')
            self.assertEqual(record['scoring_bridge_status'], 'ok')

    def test_bridge_v2_endpoint_duplicate_conflict_visible(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            ledger_path = temp_root / 'bridge_v2_ledger.jsonl'

            prediction_records = [{
                'prediction_report_id': 'rpt_conflict_1',
                'fight_id': 'theta_vs_iota',
                'predicted_winner_id': 'Theta',
                'predicted_method': 'Decision',
                'predicted_round': 'R3',
                'confidence': 0.75,
            }]
            actual_records = [{
                'fight_id': 'theta_vs_iota',
                'actual_winner': 'Theta',
                'actual_method': 'Decision',
                'actual_round': 'R3',
            }]
            ledger_rows = [
                {
                    'global_ledger_record_id': 'glr_conflict_1a',
                    'local_result_key': 'theta_vs_iota',
                    'official_source_reference': {'source_url': 'https://ufc.com/event/1'},
                    'approved_actual_result': {'fight_id': 'theta_vs_iota', 'actual_winner': 'Theta'},
                },
                {
                    'global_ledger_record_id': 'glr_conflict_1b',
                    'local_result_key': 'theta_vs_iota',
                    'official_source_reference': {'source_url': 'https://ufc.com/event/1'},
                    'approved_actual_result': {'fight_id': 'theta_vs_iota', 'actual_winner': 'Theta'},
                },
            ]

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)
            self._write_bridge_v2_fixtures(temp_accuracy_dir, ledger_path, prediction_records, actual_records, ledger_rows)

            resp = self.client.get('/api/operator/report-scoring-bridge/summary')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self.assertTrue(data['ok'])
            record = data['latest_records'][0]
            self.assertFalse(record['scored'])
            self.assertEqual(record['score_outcome'], 'duplicate_conflict')
            self.assertEqual(record['scoring_bridge_status'], 'conflict')

    def test_bridge_v2_endpoint_filter_by_prediction_report_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            ledger_path = temp_root / 'bridge_v2_ledger.jsonl'

            prediction_records = [
                {'prediction_report_id': 'rpt_filter_a', 'fight_id': 'kappa_vs_lambda'},
                {'prediction_report_id': 'rpt_filter_b', 'fight_id': 'mu_vs_nu'},
            ]

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)
            self._write_bridge_v2_fixtures(temp_accuracy_dir, ledger_path, prediction_records, actual_records=[], ledger_rows=[])

            resp = self.client.get('/api/operator/report-scoring-bridge/summary?prediction_report_id=rpt_filter_a')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self.assertTrue(data['ok'])
            self.assertEqual(data['total_records'], 1)
            self.assertEqual(data['latest_records'][0]['prediction_report_id'], 'rpt_filter_a')

    def test_bridge_v2_endpoint_filter_by_local_result_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            ledger_path = temp_root / 'bridge_v2_ledger.jsonl'

            prediction_records = [
                {'prediction_report_id': 'rpt_lrk_a', 'fight_id': 'xi_vs_omicron'},
                {'prediction_report_id': 'rpt_lrk_b', 'fight_id': 'pi_vs_rho'},
            ]

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)
            self._write_bridge_v2_fixtures(temp_accuracy_dir, ledger_path, prediction_records, actual_records=[], ledger_rows=[])

            resp = self.client.get('/api/operator/report-scoring-bridge/summary?local_result_key=xi_vs_omicron')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self.assertTrue(data['ok'])
            self.assertEqual(data['total_records'], 1)
            self.assertEqual(data['latest_records'][0]['local_result_key'], 'xi_vs_omicron')

    def test_bridge_v2_endpoint_limit_parameter_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            ledger_path = temp_root / 'bridge_v2_ledger.jsonl'

            prediction_records = [
                {'prediction_report_id': f'rpt_lim_{i}', 'fight_id': f'fight_{i}_vs_opp'}
                for i in range(5)
            ]

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)
            self._write_bridge_v2_fixtures(temp_accuracy_dir, ledger_path, prediction_records, actual_records=[], ledger_rows=[])

            resp = self.client.get('/api/operator/report-scoring-bridge/summary?limit=2')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()

            self.assertTrue(data['ok'])
            self.assertEqual(data['total_records'], 5)
            self.assertEqual(len(data['latest_records']), 2)

    def test_bridge_v2_endpoint_exposes_no_mutation_behavior(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_accuracy_dir = temp_root / 'accuracy'
            ledger_path = temp_root / 'bridge_v2_ledger.jsonl'

            prediction_records = [{
                'prediction_report_id': 'rpt_nomut_1',
                'fight_id': 'sigma_vs_tau',
                'predicted_winner_id': 'Sigma',
                'predicted_method': 'Decision',
                'predicted_round': 'R3',
                'confidence': 0.60,
            }]
            actual_records = [{
                'fight_id': 'sigma_vs_tau',
                'actual_winner': 'Sigma',
                'actual_method': 'Decision',
                'actual_round': 'R3',
            }]
            ledger_rows = [{
                'global_ledger_record_id': 'glr_nomut_1',
                'local_result_key': 'sigma_vs_tau',
                'official_source_reference': {'source_url': 'https://ufc.com/event/test-card'},
                'approved_actual_result': {
                    'fight_id': 'sigma_vs_tau',
                    'actual_winner': 'Sigma',
                    'actual_method': 'Decision',
                    'actual_round': 'R3',
                },
            }]

            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_ACCURACY_DIR_OVERRIDE'] = str(temp_accuracy_dir)
            app.config['OFFICIAL_SOURCE_APPROVED_APPLY_GLOBAL_LEDGER_PATH_OVERRIDE'] = str(ledger_path)
            self._write_bridge_v2_fixtures(temp_accuracy_dir, ledger_path, prediction_records, actual_records, ledger_rows)

            accuracy_ledger_mtime_before = (temp_accuracy_dir / 'accuracy_ledger.json').stat().st_mtime
            actual_results_mtime_before = (temp_accuracy_dir / 'actual_results.json').stat().st_mtime
            ledger_mtime_before = Path(ledger_path).stat().st_mtime

            resp = self.client.get('/api/operator/report-scoring-bridge/summary')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data['ok'])

            self.assertEqual((temp_accuracy_dir / 'accuracy_ledger.json').stat().st_mtime, accuracy_ledger_mtime_before)
            self.assertEqual((temp_accuracy_dir / 'actual_results.json').stat().st_mtime, actual_results_mtime_before)
            self.assertEqual(Path(ledger_path).stat().st_mtime, ledger_mtime_before)


# ---------------------------------------------------------------------------
# Unit tests for planner eligibility classification logic
# These tests inject a synthetic ledger directly to isolate classification.
# ---------------------------------------------------------------------------

def _make_ledger(tmp_path: Path, rows: list) -> Path:
    p = tmp_path / "ops" / "accuracy"
    p.mkdir(parents=True, exist_ok=True)
    ledger = p / "accuracy_ledger.json"
    ledger.write_text(json.dumps(rows), encoding="utf-8")
    return ledger


class TestPlannerEligibilityClassification(unittest.TestCase):

    def _run_planner(self, rows):
        """Run the planner against a synthetic ledger in a temp directory."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger = _make_ledger(tmp_path, rows)
            # Patch _load_accuracy_ledger_rows to read from tmp ledger
            # and patch the root so source_file paths are resolved safely.
            from app import _load_accuracy_ledger_rows as real_loader
            def fake_loader(path):
                return real_loader(ledger)
            with patch("app._load_accuracy_ledger_rows", side_effect=fake_loader):
                # Also patch the root used inside the function for prediction_path checks
                with patch("app.Path") as mock_path_cls:
                    # Allow Path to work normally except when resolving repo root
                    import pathlib
                    original_path = pathlib.Path

                    class PatchedPath(pathlib.Path):
                        _flavour = pathlib.Path(".")._flavour

                    # Simpler approach: just call the real function and trust fake_loader
                    mock_path_cls.side_effect = original_path
                    return _build_structural_signal_backfill_planner()

    def _run_planner_direct(self, rows):
        """Inject rows directly via monkeypatching _load_accuracy_ledger_rows."""
        with patch("app._load_accuracy_ledger_rows", return_value=rows):
            return _build_structural_signal_backfill_planner()

    def _intermediate_row(self, fight_id, resolved=True, hit_winner=True):
        return {
            "fight_id": fight_id,
            "schema_variant": "intermediate",
            "signal_gap": None,
            "stoppage_propensity": None,
            "round_finish_tendency": None,
            "resolved_result": resolved,
            "hit_winner": hit_winner,
            "source_file": f"predictions/{fight_id}.json",
            "event_date": "UNKNOWN",
        }

    def _resolved_capable_row(self, fight_id, hit_winner=True):
        return {
            "fight_id": fight_id,
            "schema_variant": "prediction_record_v1",
            "signal_gap": None,
            "stoppage_propensity": None,
            "round_finish_tendency": None,
            "resolved_result": True,
            "hit_winner": hit_winner,
            "source_file": f"predictions/{fight_id}.json",
            "event_date": "2026-01-01",
        }

    def _unresolved_row(self, fight_id):
        return {
            "fight_id": fight_id,
            "schema_variant": "prediction_record_v1",
            "signal_gap": None,
            "stoppage_propensity": None,
            "round_finish_tendency": None,
            "resolved_result": False,
            "hit_winner": None,
            "source_file": f"predictions/{fight_id}.json",
            "event_date": None,
        }

    def test_intermediate_schema_classifies_as_blocked(self):
        """Intermediate-schema narrative records must classify as BLOCKED_NEEDS_SOURCE_VALUES."""
        rows = [self._intermediate_row("bentley_vs_saavedra_prediction")]
        result = self._run_planner_direct(rows)
        self.assertTrue(result['ok'])
        queue = result['planner']['priority_queue']
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]['eligibility_class'], 'BLOCKED_NEEDS_SOURCE_VALUES')
        self.assertFalse(queue[0]['source_values_found'])
        self.assertEqual(queue[0]['recommended_action'], 'requires_source_values_or_engine_rerun')

    def test_all_five_batch1_fights_classify_as_blocked(self):
        """All five Batch 1 intermediate fights must classify as BLOCKED_NEEDS_SOURCE_VALUES."""
        fight_ids = [
            "bentley_vs_saavedra_prediction",
            "goodman_vs_ruiz_prediction",
            "pat_brown_vs_vasil_ducar_prediction",
            "riley_vs_masternak_prediction",
            "wilder_vs_chisora_prediction",
        ]
        rows = [self._intermediate_row(fid) for fid in fight_ids]
        result = self._run_planner_direct(rows)
        self.assertTrue(result['ok'])
        self.assertTrue(result['has_data'])
        queue = result['planner']['priority_queue']
        self.assertEqual(len(queue), 5)
        for row in queue:
            self.assertEqual(row['eligibility_class'], 'BLOCKED_NEEDS_SOURCE_VALUES',
                             f"{row['fight_id']} should be BLOCKED_NEEDS_SOURCE_VALUES")
            self.assertFalse(row['source_values_found'])
        ec = result['planner']['summary']['eligibility_counts']
        self.assertEqual(ec['BLOCKED_NEEDS_SOURCE_VALUES'], 5)
        self.assertEqual(ec['READY_FOR_BACKFILL'], 0)

    def test_null_structural_without_source_values_not_ready(self):
        """Records with null structural fields and no source values must not be READY_FOR_BACKFILL."""
        rows = [self._intermediate_row("some_fight")]
        result = self._run_planner_direct(rows)
        queue = result['planner']['priority_queue']
        self.assertEqual(len(queue), 1)
        self.assertNotEqual(queue[0]['eligibility_class'], 'READY_FOR_BACKFILL')

    def test_unresolved_result_classifies_as_unresolved_pending(self):
        """Records with unresolved fight results must classify as UNRESOLVED_RESULT_PENDING."""
        rows = [self._unresolved_row("future_fight")]
        result = self._run_planner_direct(rows)
        self.assertTrue(result['ok'])
        queue = result['planner']['priority_queue']
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]['eligibility_class'], 'UNRESOLVED_RESULT_PENDING')
        self.assertEqual(queue[0]['recommended_action'], 'wait_for_result_resolution')

    def test_capable_schema_resolved_classifies_as_requires_engine_rerun(self):
        """Resolved v1 records with missing structural values classify as REQUIRES_ENGINE_RERUN."""
        rows = [self._resolved_capable_row("some_v1_fight")]
        result = self._run_planner_direct(rows)
        queue = result['planner']['priority_queue']
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]['eligibility_class'], 'REQUIRES_ENGINE_RERUN')
        self.assertEqual(queue[0]['recommended_action'], 'requires_engine_rerun_with_approval')

    def test_planner_returns_200_ok_true_has_data(self):
        """Planner must return ok:true and has_data:true when rows are present."""
        rows = [self._intermediate_row("any_fight")]
        result = self._run_planner_direct(rows)
        self.assertTrue(result['ok'])
        self.assertTrue(result['has_data'])

    def test_existing_summary_keys_backwards_compatible(self):
        """Pre-existing summary keys must still be present alongside eligibility_counts."""
        rows = [self._intermediate_row("a"), self._unresolved_row("b")]
        result = self._run_planner_direct(rows)
        summary = result['planner']['summary']
        for key in ('unresolved_needing_backfill', 'resolved_needing_backfill',
                    'resolved_miss_needing_backfill', 'eligibility_counts'):
            self.assertIn(key, summary, f"Missing backwards-compat key: {key}")


# ---------------------------------------------------------------------------
# Phase 2 Premium Report Factory – Approved Save Queue Tests
# ---------------------------------------------------------------------------

class PremiumReportFactoryPhase2QueueTest(unittest.TestCase):
    """
    Focused tests for Phase 2 approved save queue behavior.
    All file I/O uses isolated temporary directories.
    No PDF, no result lookup, no learning, no web discovery.
    """

    def setUp(self):
        self.client = app.test_client()
        self._original_prf_queue_path = app.config.get('PRF_QUEUE_PATH_OVERRIDE')

    def tearDown(self):
        app.config['PRF_QUEUE_PATH_OVERRIDE'] = self._original_prf_queue_path

    def _set_temp_queue_path(self, tmpdir):
        import os
        queue_path = os.path.join(tmpdir, 'prf_queue.json')
        app.config['PRF_QUEUE_PATH_OVERRIDE'] = queue_path
        return queue_path

    def _clean_preview_payload(self):
        return {
            'raw_card_text': 'Alpha vs Beta\nGamma v Delta',
            'event_name': 'Phase2 Test Card',
            'event_date': '2026-06-01',
            'promotion': 'AI-RISA FC',
            'location': 'London',
            'source_reference': 'phase2_test_source',
            'notes': 'phase2 smoke',
        }

    def _preview_matchups(self, payload=None):
        if payload is None:
            payload = self._clean_preview_payload()
        resp = self.client.post('/api/premium-report-factory/intake/preview', json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        return data

    # 1. Phase 1 preview still works unchanged
    def test_prf_phase2_phase1_preview_still_works_unchanged(self):
        data = self._preview_matchups()
        for field in ('ok', 'generated_at', 'event_preview', 'matchup_previews', 'parse_warnings', 'errors'):
            self.assertIn(field, data)
        self.assertTrue(data.get('ok'))
        matchups = data.get('matchup_previews') or []
        self.assertEqual(len(matchups), 2)
        self.assertEqual(matchups[0].get('fighter_a'), 'Alpha')
        self.assertEqual(matchups[0].get('fighter_b'), 'Beta')
        self.assertEqual(matchups[0].get('parse_status'), 'parsed')

    # 2. No save happens on page load (GET /advanced-dashboard does not invoke save)
    def test_prf_phase2_no_save_on_page_load(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = self._set_temp_queue_path(tmpdir)
            resp = self.client.get('/advanced-dashboard')
            self.assertIn(resp.status_code, (200, 301, 302))
            import os
            self.assertFalse(os.path.exists(queue_path), 'Queue file must not be created on page load')

    # 3. Save requires explicit operator_approval
    def test_prf_phase2_save_requires_operator_approval(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            self._set_temp_queue_path(tmpdir)
            preview = self._preview_matchups()
            payload = {
                'event_preview': preview.get('event_preview'),
                'selected_matchup_previews': preview.get('matchup_previews'),
                'operator_approval': False,
                'source_reference': 'phase2_test_source',
            }
            resp = self.client.post('/api/premium-report-factory/queue/save-selected', json=payload)
            self.assertEqual(resp.status_code, 400)
            data = resp.get_json()
            self.assertFalse(data.get('ok'))
            self.assertIn('operator_approval_required', data.get('errors') or [])

    # 4. Selected valid matchups are saved
    def test_prf_phase2_selected_valid_matchups_are_saved(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = self._set_temp_queue_path(tmpdir)
            preview = self._preview_matchups()
            matchups = [m for m in (preview.get('matchup_previews') or []) if m.get('parse_status') == 'parsed']
            self.assertGreater(len(matchups), 0, 'Need at least one parsed matchup')
            payload = {
                'event_preview': preview.get('event_preview'),
                'selected_matchup_previews': matchups,
                'operator_approval': True,
                'source_reference': 'phase2_test_source',
            }
            resp = self.client.post('/api/premium-report-factory/queue/save-selected', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data.get('ok'))
            self.assertEqual(data.get('accepted_count'), len(matchups))
            self.assertEqual(data.get('rejected_count'), 0)
            saved = data.get('saved_matchups') or []
            self.assertEqual(len(saved), len(matchups))
            first = saved[0]
            for field in (
                'event_id', 'matchup_id', 'fighter_a', 'fighter_b',
                'event_name', 'event_date', 'promotion', 'location',
                'source_reference', 'bout_order', 'weight_class', 'ruleset',
                'report_readiness_score', 'report_status', 'result_status',
                'accuracy_status', 'queue_status', 'created_at',
                'approved_by_operator', 'approval_timestamp',
            ):
                self.assertIn(field, first, f'Missing field: {field}')
            self.assertTrue(first.get('approved_by_operator'))
            self.assertEqual(first.get('queue_status'), 'saved')
            for required_field in ('ok', 'generated_at', 'accepted_count', 'rejected_count',
                                   'saved_matchups', 'rejected_matchups', 'queue_summary',
                                   'warnings', 'errors'):
                self.assertIn(required_field, data)

    # 5. needs_review rows are rejected
    def test_prf_phase2_needs_review_rows_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            self._set_temp_queue_path(tmpdir)
            preview = self._preview_matchups({
                'raw_card_text': 'Alpha vs\nvs Beta',
                'event_name': 'Needs Review Card',
                'event_date': '2026-06-01',
                'source_reference': 'phase2_test_source',
            })
            matchups = preview.get('matchup_previews') or []
            needs_review = [m for m in matchups if m.get('parse_status') == 'needs_review']
            self.assertGreater(len(needs_review), 0, 'Fixture must produce at least one needs_review row')
            payload = {
                'event_preview': preview.get('event_preview'),
                'selected_matchup_previews': needs_review,
                'operator_approval': True,
                'source_reference': 'phase2_test_source',
            }
            resp = self.client.post('/api/premium-report-factory/queue/save-selected', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data.get('ok'))
            self.assertEqual(data.get('accepted_count'), 0)
            self.assertEqual(data.get('rejected_count'), len(needs_review))
            rejected = data.get('rejected_matchups') or []
            self.assertEqual(len(rejected), len(needs_review))
            for r in rejected:
                self.assertEqual(r.get('rejection_reason'), 'needs_review')

    # 6. source_reference is preserved
    def test_prf_phase2_source_reference_preserved(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            self._set_temp_queue_path(tmpdir)
            preview = self._preview_matchups()
            matchups = [m for m in (preview.get('matchup_previews') or []) if m.get('parse_status') == 'parsed']
            self.assertGreater(len(matchups), 0)
            source_ref = 'ops_sheet_phase2_2026_06_01'
            payload = {
                'event_preview': preview.get('event_preview'),
                'selected_matchup_previews': matchups,
                'operator_approval': True,
                'source_reference': source_ref,
            }
            resp = self.client.post('/api/premium-report-factory/queue/save-selected', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            for saved in data.get('saved_matchups') or []:
                self.assertEqual(saved.get('source_reference'), source_ref)

    # 7. Duplicate save is deterministic (idempotent upsert)
    def test_prf_phase2_duplicate_save_is_deterministic(self):
        import tempfile, json as _json
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = self._set_temp_queue_path(tmpdir)
            preview = self._preview_matchups()
            matchups = [m for m in (preview.get('matchup_previews') or []) if m.get('parse_status') == 'parsed']
            self.assertGreater(len(matchups), 0)
            payload = {
                'event_preview': preview.get('event_preview'),
                'selected_matchup_previews': matchups,
                'operator_approval': True,
                'source_reference': 'phase2_dedup_test',
            }
            resp1 = self.client.post('/api/premium-report-factory/queue/save-selected', json=payload)
            resp2 = self.client.post('/api/premium-report-factory/queue/save-selected', json=payload)
            self.assertEqual(resp1.status_code, 200)
            self.assertEqual(resp2.status_code, 200)

            import os
            with open(queue_path, encoding='utf-8') as f:
                rows = _json.load(f)
            # Queue should contain exactly the unique matchups, not duplicates
            matchup_ids = [r['matchup_id'] for r in rows]
            self.assertEqual(len(matchup_ids), len(set(matchup_ids)), 'Duplicate save must be idempotent')
            self.assertEqual(len(rows), len(matchups))

    # 8. Queue endpoint lists saved fights
    def test_prf_phase2_queue_endpoint_lists_saved_fights(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            self._set_temp_queue_path(tmpdir)
            # Queue empty at start
            resp_empty = self.client.get('/api/premium-report-factory/queue')
            self.assertEqual(resp_empty.status_code, 200)
            data_empty = resp_empty.get_json()
            self.assertTrue(data_empty.get('ok'))
            self.assertEqual(data_empty.get('total_queued'), 0)
            self.assertEqual(data_empty.get('upcoming_fights'), [])

            # Save one matchup
            preview = self._preview_matchups()
            matchups = [m for m in (preview.get('matchup_previews') or []) if m.get('parse_status') == 'parsed']
            self.assertGreater(len(matchups), 0)
            save_payload = {
                'event_preview': preview.get('event_preview'),
                'selected_matchup_previews': matchups[:1],
                'operator_approval': True,
                'source_reference': 'queue_list_test',
            }
            self.client.post('/api/premium-report-factory/queue/save-selected', json=save_payload)

            resp_full = self.client.get('/api/premium-report-factory/queue')
            self.assertEqual(resp_full.status_code, 200)
            data_full = resp_full.get_json()
            self.assertTrue(data_full.get('ok'))
            self.assertEqual(data_full.get('total_queued'), 1)
            fights = data_full.get('upcoming_fights') or []
            self.assertEqual(len(fights), 1)
            for field in ('ok', 'generated_at', 'total_queued', 'upcoming_fights', 'errors'):
                self.assertIn(field, data_full)

    # 9. Dashboard contains Phase 2 select controls, Save Selected button, queue window
    def test_advanced_dashboard_has_prf_phase2_select_controls(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('operator-prf-select-all', html)
        self.assertIn('operator-prf-save-selected-btn', html)
        self.assertIn('Save Selected to Upcoming Fight Queue', html)
        self.assertIn('operator-prf-matchup-checkbox', html)

    # 10. Dashboard contains queue window
    def test_advanced_dashboard_has_prf_phase2_queue_window(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('operator-prf-phase2-controls', html)
        self.assertIn('operator-prf-upcoming-queue-window', html)
        self.assertIn('operator-prf-save-queue-output', html)

    # 11. Dashboard has no PDF/result/learning controls in Phase 2 section
    def test_advanced_dashboard_prf_phase2_no_pdf_result_learning_controls(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        # Phase 2 panel must not introduce forbidden control IDs
        self.assertNotIn('operator-prf-generate-pdf-btn', html)
        self.assertNotIn('operator-prf-result-lookup-btn', html)
        self.assertNotIn('operator-prf-calibrate-btn', html)
        self.assertNotIn('operator-prf-learning-btn', html)


# ---------------------------------------------------------------------------
# Phase 3 Premium Report Factory – PDF Report Builder Tests
# ---------------------------------------------------------------------------

class PremiumReportFactoryPhase3ReportBuilderTest(unittest.TestCase):
    """
    Focused tests for Phase 3 PDF report builder.
    All file I/O uses isolated temporary directories.
    No result lookup, no accuracy comparison, no learning, no web discovery,
    no billing, no distribution.
    """

    def setUp(self):
        self.client = app.test_client()
        self._orig_queue = app.config.get('PRF_QUEUE_PATH_OVERRIDE')
        self._orig_reports = app.config.get('PRF_REPORTS_DIR_OVERRIDE')

    def tearDown(self):
        app.config['PRF_QUEUE_PATH_OVERRIDE'] = self._orig_queue
        app.config['PRF_REPORTS_DIR_OVERRIDE'] = self._orig_reports

    def _set_temp_paths(self, tmpdir):
        import os
        queue_path = os.path.join(tmpdir, 'prf_queue.json')
        reports_dir = os.path.join(tmpdir, 'prf_reports')
        app.config['PRF_QUEUE_PATH_OVERRIDE'] = queue_path
        app.config['PRF_REPORTS_DIR_OVERRIDE'] = reports_dir
        return queue_path, reports_dir

    def _save_two_matchups(self, queue_path):
        """Save two clean matchups to the queue and return their matchup_ids."""
        preview_payload = {
            'raw_card_text': 'John Fighter vs Mark Boxer\nSam Striker v Luke Grappler',
            'event_name': 'Phase3 Test Card',
            'event_date': '2026-07-01',
            'promotion': 'AI-RISA FC',
            'location': 'London',
            'source_reference': 'phase3_test_source',
            'notes': 'phase3 smoke',
        }
        resp = self.client.post('/api/premium-report-factory/intake/preview', json=preview_payload)
        self.assertEqual(resp.status_code, 200)
        preview = resp.get_json()
        matchups = [m for m in (preview.get('matchup_previews') or []) if m.get('parse_status') == 'parsed']
        self.assertGreaterEqual(len(matchups), 1)

        save_payload = {
            'event_preview': preview.get('event_preview'),
            'selected_matchup_previews': matchups,
            'operator_approval': True,
            'source_reference': 'phase3_test_source',
        }
        resp2 = self.client.post('/api/premium-report-factory/queue/save-selected', json=save_payload)
        self.assertEqual(resp2.status_code, 200)
        saved = resp2.get_json()
        matchup_ids = [m['matchup_id'] for m in saved.get('saved_matchups') or []]
        return matchup_ids

    # 1. Generate endpoint rejects missing operator_approval
    def test_prf_phase3_generate_requires_operator_approval(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            self._set_temp_paths(tmpdir)
            payload = {
                'selected_matchup_ids': [],
                'report_type': 'single_matchup',
                'operator_approval': False,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            self.assertEqual(resp.status_code, 400)
            data = resp.get_json()
            self.assertFalse(data.get('ok'))
            self.assertIn('operator_approval_required', data.get('errors') or [])

    # 2. Selected saved queue fight exports PDF
    def test_prf_phase3_generate_exports_pdf_file(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)
            self.assertGreater(len(matchup_ids), 0)

            payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'single_matchup',
                'operator_approval': True,
                'export_format': 'pdf',
                'allow_draft': True,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data.get('ok'))
            self.assertGreaterEqual(data.get('accepted_count'), 1)

            gen_reports = data.get('generated_reports') or []
            self.assertGreater(len(gen_reports), 0)
            file_path = gen_reports[0].get('file_path')
            self.assertIsNotNone(file_path)
            self.assertTrue(os.path.exists(file_path), 'PDF file must exist on disk')

    # 2b. Generated report includes explicit PDF proof fields
    def test_prf_phase3_generate_includes_pdf_proof_fields(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)

            payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'single_matchup',
                'operator_approval': True,
                'export_format': 'pdf',
                'allow_draft': True,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            gen_reports = data.get('generated_reports') or []
            self.assertGreater(len(gen_reports), 0)

            report = gen_reports[0]
            self.assertTrue(report.get('generated_pdf_exists'))
            self.assertTrue(report.get('generated_pdf_openable'))
            self.assertTrue(str(report.get('generated_pdf_path') or '').endswith('.pdf'))
            self.assertGreater(int(report.get('generated_pdf_size_bytes') or 0), 0)
            self.assertTrue(os.path.exists(report.get('generated_pdf_path')))
            self.assertEqual(report.get('report_quality_status'), 'draft_only')
            self.assertFalse(report.get('customer_ready'))
            self.assertIsInstance(report.get('missing_sections'), list)
            self.assertEqual(report.get('analysis_source_status'), 'found')
            self.assertEqual(report.get('analysis_source_type'), 'generated_internal_draft')
            self.assertEqual(report.get('missing_sections'), [])
            self.assertEqual(report.get('sparse_completion_status'), 'complete')
            self.assertEqual(report.get('sparse_completion_reason'), 'all_sparse_prediction_fields_present')
            self.assertEqual(report.get('readiness_gate_reason'), 'internal_draft_requires_operator_review')
            self.assertEqual(report.get('export_error'), '')

    def test_prf_phase3_content_preview_rows_present_for_blocked_customer_mode(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)

            payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'single_matchup',
                'operator_approval': True,
                'export_format': 'pdf',
                'allow_draft': False,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            self.assertEqual(resp.status_code, 400)
            data = resp.get_json()
            previews = data.get('content_preview_rows') or []
            self.assertEqual(len(previews), 1)
            self.assertEqual(previews[0].get('analysis_source_status'), 'not_found')
            self.assertEqual(previews[0].get('report_quality_status'), 'blocked_missing_analysis')
            self.assertTrue((previews[0].get('missing_sections') or []))
            self.assertEqual(previews[0].get('sparse_completion_status'), 'incomplete')
            self.assertIn('missing_fields:', previews[0].get('sparse_completion_reason') or '')
            self.assertEqual(previews[0].get('readiness_gate_reason'), 'missing_required_outputs_or_analysis')
            self.assertIn(previews[0].get('combat_content_status'), ('missing', 'partial'))
            self.assertIsInstance(previews[0].get('combat_engine_contributions'), dict)
            self.assertIsInstance(previews[0].get('populated_sections'), list)
            self.assertIsInstance(previews[0].get('missing_engine_outputs'), list)
            self.assertIsInstance(previews[0].get('section_source_map'), dict)
            self.assertIn('Prediction unavailable', previews[0].get('headline_prediction_preview') or '')

    def test_prf_phase3_linked_matchup_analysis_can_be_customer_ready(self):
        import tempfile
        from operator_dashboard.prf_report_builder import generate_reports

        records = [{
            'matchup_id': 'jafel_filho_vs_cody_durden',
            'fighter_a': 'Jafel Filho',
            'fighter_b': 'Cody Durden',
            'event_id': 'event_ufc_fn_moicano_duncan_2026_04_04',
            'event_name': 'UFC Fight Night: Moicano vs Duncan',
            'event_date': '2026-04-04',
            'promotion': 'UFC',
            'queue_status': 'saved',
            'source_reference': 'matchups/jafel_filho_vs_cody_durden_premium_sections.json',
            'notes': 'operator reviewed',
        }]

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_reports(
                queue_records=records,
                report_type='single_matchup',
                operator_approval=True,
                export_format='pdf',
                notes='',
                reports_dir=tmpdir,
                allow_draft=False,
            )

        self.assertTrue(result.get('ok'))
        self.assertEqual(result.get('accepted_count'), 1)
        report = (result.get('generated_reports') or [])[0]
        self.assertEqual(report.get('report_quality_status'), 'customer_ready')
        self.assertTrue(report.get('customer_ready'))
        self.assertEqual(report.get('analysis_source_status'), 'found')
        self.assertEqual(report.get('analysis_source_type'), 'analysis_json')
        self.assertIn('premium_sections', str(report.get('linked_analysis_record_id') or ''))
        self.assertEqual(report.get('missing_sections'), [])
        self.assertEqual(report.get('sparse_completion_status'), 'complete')
        self.assertEqual(report.get('sparse_completion_reason'), 'all_sparse_prediction_fields_present')
        self.assertEqual(report.get('readiness_gate_reason'), 'all_required_outputs_present')
        self.assertEqual(report.get('combat_content_status'), 'complete')
        self.assertIsInstance(report.get('combat_engine_contributions'), dict)
        self.assertIsInstance(report.get('populated_sections'), list)
        self.assertIsInstance(report.get('missing_engine_outputs'), list)
        self.assertIsInstance(report.get('section_source_map'), dict)
        self.assertEqual(report.get('missing_engine_outputs'), [])
        self.assertIn('headline_prediction', report.get('populated_sections') or [])

    def test_prf_phase3_internal_draft_content_has_no_unavailable_placeholders(self):
        from operator_dashboard.prf_report_content import build_report_content_bundle

        bundle = build_report_content_bundle({
            'matchup_id': 'prf_q_internal001',
            'fighter_a': 'John Fighter',
            'fighter_b': 'Mark Boxer',
            'event_name': 'Internal Draft Test',
            'event_date': '2026-07-01',
            'promotion': 'AI-RISA FC',
            'source_reference': 'phase3_test_source',
            'notes': '',
        }, allow_internal_draft=True)

        sections = bundle.get('sections') or {}
        self.assertEqual(bundle.get('analysis_source_type'), 'generated_internal_draft')
        for key in [
            'headline_prediction',
            'decision_structure',
            'energy_use',
            'fatigue_failure_points',
            'mental_condition',
            'collapse_triggers',
            'deception_and_unpredictability',
            'round_by_round_control_shifts',
            'scenario_tree',
        ]:
            self.assertTrue(str(sections.get(key) or '').strip())
            self.assertNotIn('unavailable', str(sections.get(key) or '').lower())

    def test_prf_phase3_blocked_missing_analysis_when_draft_disabled(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)

            payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'single_matchup',
                'operator_approval': True,
                'export_format': 'pdf',
                'allow_draft': False,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            self.assertEqual(resp.status_code, 400)
            data = resp.get_json()
            self.assertFalse(data.get('ok'))
            self.assertEqual(data.get('accepted_count'), 0)
            rejected = data.get('rejected_reports') or []
            self.assertEqual(len(rejected), 1)
            self.assertEqual(rejected[0].get('report_quality_status'), 'blocked_missing_analysis')
            self.assertEqual(rejected[0].get('sparse_completion_status'), 'incomplete')
            self.assertIn('missing_fields:', rejected[0].get('sparse_completion_reason') or '')
            self.assertEqual(rejected[0].get('readiness_gate_reason'), 'missing_required_outputs_or_analysis')
            self.assertIn(rejected[0].get('combat_content_status'), ('missing', 'partial'))
            self.assertIsInstance(rejected[0].get('combat_engine_contributions'), dict)
            self.assertIsInstance(rejected[0].get('populated_sections'), list)
            self.assertIsInstance(rejected[0].get('missing_engine_outputs'), list)
            self.assertIsInstance(rejected[0].get('section_source_map'), dict)
            self.assertGreater(len(rejected[0].get('missing_engine_outputs') or []), 0)
            self.assertIn(
                'Cannot generate customer PDF yet. Analysis data is missing for this matchup.',
                rejected[0].get('reason') or '',
            )

    def test_prf_phase3_default_customer_mode_blocks_missing_analysis(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)

            payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'single_matchup',
                'operator_approval': True,
                'export_format': 'pdf',
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            self.assertEqual(resp.status_code, 400)
            data = resp.get_json()
            self.assertFalse(data.get('ok'))
            rejected = data.get('rejected_reports') or []
            self.assertEqual(len(rejected), 1)
            self.assertEqual(rejected[0].get('report_quality_status'), 'blocked_missing_analysis')

    # 3. Deterministic filename
    def test_prf_phase3_deterministic_filename(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)
            self.assertGreater(len(matchup_ids), 0)

            payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'single_matchup',
                'operator_approval': True,
                'allow_draft': True,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            gen_reports = data.get('generated_reports') or []
            self.assertGreater(len(gen_reports), 0)
            file_name = gen_reports[0].get('file_name')
            self.assertIsNotNone(file_name)
            self.assertTrue(file_name.startswith('ai_risa_premium_report_'), 'Filename must use deterministic prefix')
            self.assertTrue(file_name.endswith('.pdf'), 'Filename must end with .pdf')

    def test_prf_phase3_filename_sanitizes_windows_invalid_characters(self):
        from operator_dashboard.prf_report_export import build_report_filename

        file_name = build_report_filename('ares_fc_39: jbalia vs. diatta', 'prf_q_7b1e2a0d1275b54a')

        self.assertTrue(file_name.endswith('.pdf'))
        self.assertNotIn(':', file_name)
        self.assertNotIn('/', file_name)
        self.assertNotIn('\\', file_name)
        self.assertIn('ares_fc_39__jbalia_vs._diatta', file_name)

    # 4. report_status is 'generated' only after confirmed file write
    def test_prf_phase3_report_status_generated_only_after_success(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)
            self.assertGreater(len(matchup_ids), 0)

            payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'single_matchup',
                'operator_approval': True,
                'allow_draft': True,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            data = resp.get_json()
            for rep in data.get('generated_reports') or []:
                self.assertIn(
                    rep.get('report_status'),
                    ('generated', 'partial'),
                    'report_status must be generated or partial, not pending or failed',
                )
                self.assertNotEqual(rep.get('report_status'), 'pending')
                self.assertNotEqual(rep.get('report_status'), 'failed')

    # 5. Failed export does not mark report_status as 'generated'
    def test_prf_phase3_failed_export_not_marked_generated(self):
        from operator_dashboard.prf_report_builder import generate_reports
        # Use an invalid reports_dir to trigger export failure
        records = [{
            'matchup_id': 'prf_q_test001',
            'fighter_a': 'Alpha',
            'fighter_b': 'Beta',
            'event_id': 'alpha_event',
            'event_name': 'Alpha Event',
            'event_date': '2026-07-01',
            'promotion': 'Test FC',
            'queue_status': 'saved',
            'source_reference': 'test',
            'notes': '',
        }]
        # Pass a path where writing is impossible (a file, not a dir)
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a *file* where the reports dir would be to force failure
            bad_dir = os.path.join(tmpdir, 'not_a_dir')
            with open(bad_dir, 'w') as f:
                f.write("block")
            result = generate_reports(
                queue_records=records,
                report_type='single_matchup',
                operator_approval=True,
                export_format='pdf',
                notes='',
                reports_dir=bad_dir,
            )
        # ok is False because accepted_count == 0
        self.assertFalse(result.get('ok'))
        self.assertEqual(result.get('accepted_count'), 0)
        # Verify no generated_reports have status 'generated'
        for rep in result.get('generated_reports') or []:
            self.assertNotEqual(rep.get('report_status'), 'generated')

    # 5b. Invalid export artifacts are not treated as generated PDFs
    def test_prf_phase3_non_pdf_or_zero_byte_artifact_not_marked_generated(self):
        import tempfile
        from unittest.mock import patch
        from operator_dashboard.prf_report_builder import generate_reports

        records = [{
            'matchup_id': 'prf_q_test002',
            'fighter_a': 'Alpha',
            'fighter_b': 'Beta',
            'event_id': 'alpha_event',
            'event_name': 'Alpha Event',
            'event_date': '2026-07-01',
            'promotion': 'Test FC',
            'queue_status': 'saved',
            'source_reference': 'test',
            'notes': '',
        }]

        with tempfile.TemporaryDirectory() as tmpdir:
            zero_byte_path = os.path.join(tmpdir, 'broken_export.pdf')

            def _fake_write_pdf_report(report_obj, sections, reports_dir):
                with open(zero_byte_path, 'wb'):
                    pass
                return {
                    'ok': True,
                    'file_path': zero_byte_path,
                    'file_name': os.path.basename(zero_byte_path),
                    'error': None,
                }

            with patch('operator_dashboard.prf_report_builder.write_pdf_report', _fake_write_pdf_report):
                result = generate_reports(
                    queue_records=records,
                    report_type='single_matchup',
                    operator_approval=True,
                    export_format='pdf',
                    notes='',
                    reports_dir=tmpdir,
                    allow_draft=True,
                )

        self.assertFalse(result.get('ok'))
        self.assertEqual(result.get('accepted_count'), 0)
        self.assertEqual(len(result.get('generated_reports') or []), 0)
        self.assertEqual(len(result.get('rejected_reports') or []), 1)
        self.assertTrue(any('Zero-byte PDF file detected' in err for err in (result.get('errors') or [])))

    # 6. All 14 required sections present in section_status
    def test_prf_phase3_all_14_sections_present(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)
            self.assertGreater(len(matchup_ids), 0)

            payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'single_matchup',
                'operator_approval': True,
                'allow_draft': True,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            data = resp.get_json()
            gen_reports = data.get('generated_reports') or []
            self.assertGreater(len(gen_reports), 0)
            section_status = gen_reports[0].get('section_status') or {}
            required_sections = [
                'cover_page', 'headline_prediction', 'executive_summary',
                'matchup_snapshot', 'decision_structure', 'energy_use',
                'fatigue_failure_points', 'mental_condition', 'collapse_triggers',
                'deception_and_unpredictability', 'round_by_round_control_shifts',
                'scenario_tree', 'risk_warnings', 'operator_notes',
            ]
            for section in required_sections:
                self.assertIn(section, section_status, 'Missing section: {}'.format(section))

    # 7. section_status values are valid
    def test_prf_phase3_section_status_values_valid(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)
            self.assertGreater(len(matchup_ids), 0)

            payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'single_matchup',
                'operator_approval': True,
                'allow_draft': True,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            data = resp.get_json()
            gen_reports = data.get('generated_reports') or []
            section_status = gen_reports[0].get('section_status') or {}
            valid_values = {'complete', 'partial', 'unavailable', 'blocked'}
            for section, status in section_status.items():
                self.assertIn(status, valid_values, 'Invalid section_status value for {}: {}'.format(section, status))

    # 8. Missing analysis uses empty-state placeholders (not blank)
    def test_prf_phase3_empty_state_placeholders_not_blank(self):
        from operator_dashboard.prf_report_content import assemble_report_sections
        record = {
            'matchup_id': 'prf_q_test002',
            'fighter_a': 'NoData Fighter One',
            'fighter_b': 'NoData Fighter Two',
            'event_id': 'test_event',
            'event_name': 'Test Event',
            'event_date': '2026-07-01',
            'promotion': 'Test FC',
            'queue_status': 'saved',
            'source_reference': 'no_linked_analysis_expected',
            'notes': '',
        }
        sections, section_status = assemble_report_sections(record)
        # Sections that will be 'unavailable' in Phase 3 must have explicit placeholder text
        unavailable_sections = [
            'headline_prediction', 'decision_structure', 'energy_use',
            'fatigue_failure_points', 'mental_condition', 'collapse_triggers',
            'deception_and_unpredictability', 'round_by_round_control_shifts', 'scenario_tree',
        ]
        for section in unavailable_sections:
            content = sections.get(section) or ''
            self.assertTrue(bool(content.strip()), 'Section {} must have non-empty placeholder'.format(section))
            self.assertNotEqual(content.strip(), '', 'Section {} must not be blank'.format(section))
            self.assertEqual(section_status.get(section), 'unavailable')

    # 9. Unsupported report_type is rejected
    def test_prf_phase3_unsupported_report_type_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)

            payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'totally_invalid_type',
                'operator_approval': True,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            self.assertEqual(resp.status_code, 400)
            data = resp.get_json()
            self.assertFalse(data.get('ok'))
            errors = data.get('errors') or []
            self.assertTrue(any('unsupported_report_type' in e for e in errors))

    # 10. fighter_profile report_type is rejected in Phase 3
    def test_prf_phase3_fighter_profile_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)

            payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'fighter_profile',
                'operator_approval': True,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            self.assertEqual(resp.status_code, 400)
            data = resp.get_json()
            self.assertFalse(data.get('ok'))
            errors = data.get('errors') or []
            self.assertTrue(any('not_supported' in e for e in errors))

    # 11. Report list endpoint returns generated reports
    def test_prf_phase3_report_list_endpoint(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)

            # List is empty before generation
            resp = self.client.get('/api/premium-report-factory/reports/list')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data.get('ok'))
            self.assertEqual(data.get('total_count'), 0)
            self.assertEqual(data.get('reports'), [])

            # Generate a report
            matchup_ids = self._save_two_matchups(queue_path)
            gen_payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'single_matchup',
                'operator_approval': True,
                'allow_draft': True,
            }
            self.client.post('/api/premium-report-factory/reports/generate', json=gen_payload)

            # List now shows the generated report
            resp2 = self.client.get('/api/premium-report-factory/reports/list')
            self.assertEqual(resp2.status_code, 200)
            data2 = resp2.get_json()
            self.assertTrue(data2.get('ok'))
            self.assertGreaterEqual(data2.get('total_count'), 1)
            for field in ('ok', 'generated_at', 'reports', 'total_count', 'warnings', 'errors'):
                self.assertIn(field, data2)

    def test_prf_phase3_download_endpoint_returns_pdf(self):
        import tempfile
        from urllib.parse import quote

        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)

            gen_payload = {
                'selected_matchup_ids': matchup_ids[:1],
                'report_type': 'single_matchup',
                'operator_approval': True,
                'allow_draft': True,
            }
            gen_resp = self.client.post('/api/premium-report-factory/reports/generate', json=gen_payload)
            self.assertEqual(gen_resp.status_code, 200)
            generated = (gen_resp.get_json().get('generated_reports') or [])[0]
            report_id = generated.get('report_id')
            file_name = generated.get('file_name')

            dl_resp = self.client.get(
                '/api/premium-report-factory/reports/download/{}?file_name={}'.format(
                    quote(str(report_id), safe=''),
                    quote(str(file_name), safe=''),
                ),
                buffered=True,
            )
            self.assertEqual(dl_resp.status_code, 200)
            self.assertEqual(dl_resp.mimetype, 'application/pdf')
            self.assertGreater(len(dl_resp.data), 0)
            dl_resp.close()

    def test_prf_phase3_open_reports_folder_endpoint(self):
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            os.makedirs(reports_dir, exist_ok=True)

            with patch('operator_dashboard.app.os.startfile') as mocked_startfile:
                ok_resp = self.client.post(
                    '/api/premium-report-factory/reports/open-folder',
                    json={'folder_path': reports_dir},
                )
                self.assertEqual(ok_resp.status_code, 200)
                ok_data = ok_resp.get_json()
                self.assertTrue(ok_data.get('ok'))
                mocked_startfile.assert_called_once()

            bad_resp = self.client.post(
                '/api/premium-report-factory/reports/open-folder',
                json={'folder_path': os.path.abspath(os.path.join(reports_dir, '..'))},
            )
            self.assertEqual(bad_resp.status_code, 400)
            bad_data = bad_resp.get_json()
            self.assertFalse(bad_data.get('ok'))
            self.assertIn('invalid_folder_path', bad_data.get('errors') or [])

    # 12. Dashboard contains Generate Premium PDF Reports button
    def test_prf_phase3_dashboard_has_generate_btn(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('operator-prf-generate-reports-btn', html)
        self.assertIn('Generate Premium PDF Reports', html)

    # 13. Dashboard contains export results window
    def test_prf_phase3_dashboard_has_export_results_window(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('operator-prf-export-results-window', html)
        self.assertIn('operator-prf-generate-approval', html)
        self.assertIn('operator-prf-report-type-select', html)
        self.assertIn('operator-prf-generate-warnings', html)

    def test_prf_phase3_index_has_download_and_quality_controls(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('main-prf-allow-draft', html)
        self.assertIn('Generate internal draft only', html)
        self.assertIn('Analysis Source', html)
        self.assertIn('Content Preview Before Export', html)
        self.assertIn('Download PDF', html)
        self.assertIn('Open Reports Folder', html)
        self.assertIn('Copy PDF Path', html)

    # 14. Dashboard contains no result/learning/billing/web controls
    def test_prf_phase3_dashboard_no_forbidden_controls(self):
        resp = self.client.get('/advanced-dashboard')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertNotIn('operator-prf-result-lookup-btn', html)
        self.assertNotIn('operator-prf-calibrate-btn', html)
        self.assertNotIn('operator-prf-learning-btn', html)
        self.assertNotIn('operator-prf-billing-btn', html)
        self.assertNotIn('operator-prf-web-discover-btn', html)
        self.assertNotIn('operator-prf-email-btn', html)

    # 15. Backend regression: Phase 2 queue still works after Phase 3 additions
    def test_prf_phase3_phase2_regression(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            self._set_temp_paths(tmpdir)
            # Phase 1 preview
            resp = self.client.post('/api/premium-report-factory/intake/preview', json={
                'raw_card_text': 'Alpha vs Beta',
                'event_name': 'Regression Card',
                'event_date': '2026-07-01',
                'source_reference': 'regression_test',
            })
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(resp.get_json().get('ok'))
            # Phase 2 save
            preview = resp.get_json()
            matchups = [m for m in (preview.get('matchup_previews') or []) if m.get('parse_status') == 'parsed']
            if matchups:
                save_resp = self.client.post('/api/premium-report-factory/queue/save-selected', json={
                    'event_preview': preview.get('event_preview'),
                    'selected_matchup_previews': matchups,
                    'operator_approval': True,
                    'source_reference': 'regression_test',
                })
                self.assertEqual(save_resp.status_code, 200)
                self.assertTrue(save_resp.get_json().get('ok'))
            # Phase 2 queue list
            list_resp = self.client.get('/api/premium-report-factory/queue')
            self.assertEqual(list_resp.status_code, 200)
            self.assertTrue(list_resp.get_json().get('ok'))

    # 16. Full event-card report generation from multiple saved queue fights
    def test_prf_phase3_event_card_multi_matchup_batch(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path, reports_dir = self._set_temp_paths(tmpdir)
            matchup_ids = self._save_two_matchups(queue_path)
            self.assertGreaterEqual(len(matchup_ids), 2)

            payload = {
                'selected_matchup_ids': matchup_ids,
                'report_type': 'event_card',
                'operator_approval': True,
                'notes': 'batch event card test',
                'allow_draft': True,
            }
            resp = self.client.post('/api/premium-report-factory/reports/generate', json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data.get('ok'))
            self.assertGreaterEqual(data.get('accepted_count'), 1)

            gen_reports = data.get('generated_reports') or []
            for rep in gen_reports:
                self.assertIsNotNone(rep.get('file_path'))
                self.assertTrue(os.path.exists(rep['file_path']), 'PDF must exist: {}'.format(rep['file_path']))

if __name__ == '__main__':
    unittest.main()


class EnginePackRegistryWiringTest(unittest.TestCase):
    """
    Focused tests for engine-pack registry wiring (display-only, additive keys).
    Verifies that new availability keys appear in responses without disrupting
    existing response key access or behavior.
    No PDF, no writes, no calibration behavior changes.
    """

    def setUp(self):
        self.client = app.test_client()
        self._original_prf_queue_path = app.config.get('PRF_QUEUE_PATH_OVERRIDE')
        self._original_prf_reports_dir = app.config.get('PRF_REPORTS_DIR_OVERRIDE')

    def tearDown(self):
        app.config['PRF_QUEUE_PATH_OVERRIDE'] = self._original_prf_queue_path
        app.config['PRF_REPORTS_DIR_OVERRIDE'] = self._original_prf_reports_dir

    # 1. Button 1 queue route has ranking_engine_availability
    def test_button1_queue_has_ranking_engine_availability(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, 'prf_queue.json')
            app.config['PRF_QUEUE_PATH_OVERRIDE'] = queue_path
            resp = self.client.get('/api/premium-report-factory/queue')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn('ranking_engine_availability', data)
            availability = data['ranking_engine_availability']
            self.assertIsInstance(availability, list)
            self.assertGreater(len(availability), 0)

    # 2. ranking_engine_availability entries have required fields
    def test_button1_ranking_availability_entry_shape(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, 'prf_queue.json')
            app.config['PRF_QUEUE_PATH_OVERRIDE'] = queue_path
            resp = self.client.get('/api/premium-report-factory/queue')
            data = resp.get_json()
            entry = data['ranking_engine_availability'][0]
            self.assertIn('engine_id', entry)
            self.assertIn('label', entry)
            self.assertIn('required', entry)
            self.assertIn('active', entry)
            self.assertTrue(entry['active'])

    # 3. Button 1 queue route existing key 'ok' is preserved after wiring
    def test_button1_queue_existing_ok_key_preserved(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, 'prf_queue.json')
            app.config['PRF_QUEUE_PATH_OVERRIDE'] = queue_path
            resp = self.client.get('/api/premium-report-factory/queue')
            data = resp.get_json()
            self.assertIn('ok', data)

    # 4. Button 3 calibration route has calibration_engine_availability
    def test_button3_calibration_review_has_calibration_engine_availability(self):
        resp = self.client.post('/api/operator/accuracy-calibration-review', json={})
        data = resp.get_json()
        self.assertIn('calibration_engine_availability', data)
        availability = data['calibration_engine_availability']
        self.assertIsInstance(availability, list)
        self.assertGreater(len(availability), 0)

    # 5. calibration_engine_availability entries have approval_gate_required field
    def test_button3_calibration_availability_entry_shape(self):
        resp = self.client.post('/api/operator/accuracy-calibration-review', json={})
        data = resp.get_json()
        entry = data['calibration_engine_availability'][0]
        self.assertIn('engine_id', entry)
        self.assertIn('label', entry)
        self.assertIn('required', entry)
        self.assertIn('approval_gate_required', entry)
        self.assertIn('active', entry)

    # 6. Button 3 existing approval_required key is preserved after wiring
    def test_button3_existing_approval_required_key_preserved(self):
        resp = self.client.post('/api/operator/accuracy-calibration-review', json={})
        data = resp.get_json()
        self.assertIn('approval_required', data)
        self.assertTrue(data['approval_required'])

    # 7. Engine registry manifest endpoint returns ok and engines list
    def test_engine_registry_manifest_returns_ok_and_engines(self):
        resp = self.client.get('/api/engine-registry-manifest')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('engines', data)
        self.assertIsInstance(data['engines'], list)
        self.assertGreater(len(data['engines']), 0)

    # 8. Engine registry manifest entries have expected shape
    def test_engine_registry_manifest_entry_shape(self):
        resp = self.client.get('/api/engine-registry-manifest')
        data = resp.get_json()
        entry = data['engines'][0]
        self.assertIn('engine_id', entry)
        self.assertIn('engine_group', entry)
        self.assertIn('display_name', entry)
        self.assertIn('buttons', entry)
        self.assertIn('approval_gate_required', entry)

    # 9. Button 2 generate route has engine_availability after approved generate
    def test_button2_generate_has_engine_availability(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, 'prf_queue.json')
            reports_dir = os.path.join(tmpdir, 'reports')
            app.config['PRF_QUEUE_PATH_OVERRIDE'] = queue_path
            app.config['PRF_REPORTS_DIR_OVERRIDE'] = reports_dir
            resp = self.client.post('/api/premium-report-factory/reports/generate', json={
                'operator_approval': True,
                'allow_draft': True,
            })
            data = resp.get_json()
            self.assertIn('engine_availability', data)
            ea = data['engine_availability']
            self.assertIn('betting_engines', ea)
            self.assertIn('generation_engines', ea)
            self.assertIn('section_manifest', ea)
            self.assertIn('report_readiness_preview', ea)
            self.assertEqual(ea['report_readiness_preview'], 'unavailable')

    # 10. Button 2 generate route existing ok key preserved after wiring
    def test_button2_generate_existing_ok_key_preserved(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, 'prf_queue.json')
            reports_dir = os.path.join(tmpdir, 'reports')
            app.config['PRF_QUEUE_PATH_OVERRIDE'] = queue_path
            app.config['PRF_REPORTS_DIR_OVERRIDE'] = reports_dir
            resp = self.client.post('/api/premium-report-factory/reports/generate', json={
                'operator_approval': True,
                'allow_draft': True,
            })
            data = resp.get_json()
            self.assertIn('ok', data)


if __name__ == '__main__':
    unittest.main()
