import sys, json

f1, f2 = sys.argv[1], sys.argv[2]
matchup_file = f'C:/ai_risa_data/matchups/{f1.lower().replace(" ", "_")}_vs_{f2.lower().replace(" ", "_")}.json'
with open(matchup_file, 'r', encoding='utf-8') as f:
    matchup = json.load(f)
# Minimal prediction logic
pred = {
    'predicted_winner': f1,
    'method_tendency': 'Decision',
    'confidence': 0.6,
    'tactical_interaction': 'Standard AI-RISA logic',
    'round_flow_projection': 'Likely to go full rounds'
}
out_path = f'C:/ai_risa_data/predictions/{f1.lower().replace(" ", "_")}_vs_{f2.lower().replace(" ", "_")}_prediction.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(pred, f, indent=2)
print(f'Prediction written: {out_path}')
