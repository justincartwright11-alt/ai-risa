from pdfminer.high_level import extract_text
import re

pdf_path = r'C:\ai_risa_data\reports\bahram_rajabzadeh_vs_donovan_wisse_premium.pdf'
patterns = ['fighter_', 'Unknown', 'N/A', 'Prochazka:', 'Ulberg:', 'Confidence']

try:
    text = extract_text(pdf_path)
    found = False
    lines = text.split('\n')
    for i, line in enumerate(lines):
        for pattern in patterns:
            if pattern in line:
                print(f'Match: "{pattern}" at line {i+1}: {line.strip()}')
                found = True
    if not found:
        print('Clean')
except Exception as e:
    print(f'Error: {e}')
