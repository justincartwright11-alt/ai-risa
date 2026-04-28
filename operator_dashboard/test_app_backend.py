import unittest
import json
import os
import tempfile
import hashlib
import uuid
from pathlib import Path
from unittest.mock import patch
from time import time
from app import (
    app,
    _build_structural_signal_backfill_planner,
    _build_batch_preview_execution_token,
    _build_selected_keys_digest,
    _is_allowed_official_source_url,
    _classify_official_source_host,
    _build_citation_fingerprint,
    _classify_source_confidence,
    _validate_official_source_citation,
)

class DashboardBackendTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def _official_preview_payload(self, selected_key='alpha_vs_beta|predictions_alpha_vs_beta_prediction_json', **overrides):
        payload = {
            'selected_key': selected_key,
            'mode': 'official_source_one_record',
            'lookup_intent': 'preview_only',
            'approval_granted': False,
        }
        payload.update(overrides)
        return payload

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

    @patch('app._upsert_single_manual_actual_result')
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_official_source_one_record_preview_valid_selected_key_returns_preview_only_flags(self, mock_summary, mock_local_map, mock_upsert):
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
        self.assertFalse(data.get('external_lookup_performed'))
        self.assertTrue(data.get('manual_review_required'))
        self.assertFalse(data.get('local_result_found'))
        self.assertIsNone(data.get('proposed_write'))
        self.assertIsNone(data.get('source_citation'))
        self.assertEqual((data.get('audit') or {}).get('reason_code'), 'official_source_lookup_not_connected')
        mock_upsert.assert_not_called()

    @patch('app._upsert_single_manual_actual_result')
    @patch('app._load_local_actual_result_map')
    @patch('app._build_accuracy_comparison_summary')
    def test_official_source_one_record_preview_local_result_found_still_does_not_mutate(self, mock_summary, mock_local_map, mock_upsert):
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
        mock_upsert.assert_not_called()

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

    def test_no_ui_template_references_official_source_preview_endpoint_yet(self):
        index_resp = self.client.get('/')
        self.assertEqual(index_resp.status_code, 200)
        self.assertNotIn(b'/api/operator/actual-result-lookup/official-source-one-record-preview', index_resp.data)

        advanced_resp = self.client.get('/advanced-dashboard')
        self.assertEqual(advanced_resp.status_code, 200)
        self.assertNotIn(b'/api/operator/actual-result-lookup/official-source-one-record-preview', advanced_resp.data)

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
if __name__ == '__main__':
    unittest.main()
