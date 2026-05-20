from pathlib import Path
import io
import os
import sys
from pypdf import PdfReader

root = Path(r'C:\Users\jusin\OneDrive\Documents\Custom Office Templates')
sys.path.insert(0, str(root))
from operator_dashboard import app as app_module
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer

os.environ['BUTTON2_PDF_OUTPUT_ROOT'] = str(root / 'reports')
preview = {
    'selected_matchup': {
        'fighter_a': 'Callum Walsh',
        'fighter_b': 'Austin Williams',
        'event_name': 'Joshua vs Dubois',
        'event_date': '2026-09-21',
        'promotion': 'Matchroom Boxing',
        'source_url': 'https://www.matchroomboxing.com/events/joshua-vs-dubois',
        'source_type': 'official',
    },
    'handoff_summary_preview': 'Selected matchup handoff summary.',
    'source_traceability': [{'source_url': 'https://www.matchroomboxing.com/events/joshua-vs-dubois', 'source_type': 'official', 'source_date': '2026-09-21'}],
}
out = renderer.render_button2_template_pack_asset_pdf(preview)
pdf_path = root / 'reports' / 'callum_walsh_vs_austin_williams_joshua_vs_dubois_premium_dense_page_v3.pdf'
pdf_path.write_bytes(out['pdf_bytes'])
text = '\n'.join((page.extract_text() or '') for page in PdfReader(io.BytesIO(out['pdf_bytes'])).pages)
ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(preview['selected_matchup'], {'output_path': str(pdf_path), 'output_filename': pdf_path.name, 'report_id': 'callum_walsh_vs_austin_williams_joshua_vs_dubois'}, text, 24, out.get('layout_safety'))
print('ok', ok)
print('violations', violations)
print('lens', out.get('layout_safety', {}).get('lens_depth'))
