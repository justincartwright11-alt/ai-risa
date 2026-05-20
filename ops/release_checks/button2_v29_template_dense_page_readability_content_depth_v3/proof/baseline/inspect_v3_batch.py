from pathlib import Path
import os
import sys
root = Path(r'C:\Users\jusin\OneDrive\Documents\Custom Office Templates')
sys.path.insert(0, str(root))
from operator_dashboard import app as app_module
from operator_dashboard.test_button2_v29_template_dense_page_readability_content_depth_v3 import _queue_rows, _success_text_for_selected

os.environ['BUTTON2_PDF_OUTPUT_ROOT'] = r'C:\Users\jusin\AppData\Local\Temp'
rows = _queue_rows()[:2]
text_by_path = {}

def _generate(payload):
    out_path = Path(os.environ['BUTTON2_PDF_OUTPUT_ROOT']) / payload['output_filename_override']
    selected = payload.get('ingest_payload', {}).get('selected_matchup_payload', {})
    out_path.write_bytes(b'%PDF-1.4\n')
    text_by_path[str(out_path)] = _success_text_for_selected(selected)
    return {
        'ok': True,
        'output_path': str(out_path),
        'output_filename': payload['output_filename_override'],
        'report_id': Path(payload['output_filename_override']).stem,
        'renderer_route_used': 'template_pack_asset_renderer',
        'renderer_profile': 'premium_template_pack_v29_layout_parity_rebuild_v1',
        'template_pack_asset_backed': True,
        'layout_safety': {
            'operator_note_present': False,
            'operator_note_absent_passed': True,
            'dashboard_lens_depth_passed': True,
            'round_heading_body_clear_passed': True,
            'readable_min_font_passed': True,
            'footer_safe_zone_passed': True,
            'tactical_edge_overlap_passed': True,
            'scorecard_readability_passed': True,
            'stoppage_readability_passed': True,
            'round_outlook_centered_passed': True,
            'footer_safe_zone_pages': {'6': {'safe': True}, '16': {'safe': True}, '17': {'safe': True}},
            'page_bounds': {'6': {'overlap_detected': False, 'min_font_size': 8.8}, '14': {'overlap_detected': False, 'min_font_size': 8.6}, '16': {'overlap_detected': False, 'min_font_size': 8.8}, '17': {'overlap_detected': False, 'min_font_size': 8.8}},
            'lens_depth': {'control': {'length': 120, 'mentions_selected_fighter': True, 'generic_placeholder': False, 'overflow': False}, 'danger': {'length': 120, 'mentions_selected_fighter': True, 'generic_placeholder': False, 'overflow': False}, 'command': {'length': 120, 'mentions_selected_fighter': True, 'generic_placeholder': False, 'overflow': False}},
            'source_map': {'rows_separated': True, 'source_url_statement_separated': True},
        },
        'delivery_performed': False,
        'external_api_delivery_performed': False,
        'queue_write_performed': False,
        'learning_apply_performed': False,
        'calibration_write_performed': False,
        'button3_mutation_performed': False,
    }

def _extract(path):
    return text_by_path.get(str(path), ''), 24

app_module.load_button2_queue_readonly = lambda: rows
app_module.generate_button2_report_render_gate_integration = _generate
app_module._extract_pdf_text_and_page_count = _extract
app_module.app.config['TESTING'] = True
with app_module.app.test_client() as client:
    resp = client.post('/api/button2/generate-selected-batch', json={'operator_approval': True, 'selected_matchup_ids': [row['matchup_id'] for row in rows]})
    print(resp.status_code)
    print(resp.get_json())
