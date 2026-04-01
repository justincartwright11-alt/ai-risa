import json
import os

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def predict_winner(matchup):
    # Minimal logic: favor youth, power, recent form
    f1, f2 = matchup['fighters']
    f1_data = load_json(f"C:/ai_risa_data/fighters/{f1.lower().replace(' ', '_')}.json")
    f2_data = load_json(f"C:/ai_risa_data/fighters/{f2.lower().replace(' ', '_')}.json")
    # Simple scoring
    score1 = (f1_data['age'] < f2_data['age']) + (f1_data['last_5'].count('W') > f2_data['last_5'].count('W'))
    score2 = (f2_data['age'] < f1_data['age']) + (f2_data['last_5'].count('W') > f1_data['last_5'].count('W'))
    if score1 > score2:
        winner = f1
        method = "KO/TKO likely"
        confidence = 0.7
        edge = "Power, youth"
    elif score2 > score1:
        winner = f2
        method = "Decision/late TKO"
        confidence = 0.6
        edge = "Durability, experience"
    else:
        winner = f1 if f1_data['record'] > f2_data['record'] else f2
        method = "Close decision"
        confidence = 0.5
        edge = "Even"
    # AI-RISA profile (stub)
    profile = {
        "decision_structure": "Aggressive exchanges, risk-taking",
        "energy_use": "High early, fades late",
        "fatigue_failure_points": "Late rounds, under pressure",
        "mental_condition": "Streak-dependent",
        "collapse_triggers": "Sustained body attack, pace",
        "main_tactical_edge": edge
    }
    return {
        "predicted_winner": winner,
        "method_tendency": method,
        "confidence": confidence,
        **profile
    }

def main():
    event = load_json("C:/ai_risa_data/events/boxing_o2_arena_2026_04_04.json")
    results = {}
    for matchup_file in event['matchups']:
        matchup_path = f"C:/ai_risa_data/matchups/{matchup_file}"
        matchup = load_json(matchup_path)
        try:
            prediction = predict_winner(matchup)
            out_path = f"C:/ai_risa_data/predictions/{matchup_file.replace('.json', '_prediction.json')}"
            save_json(out_path, prediction)
            results[matchup_file] = {"status": "passed", "prediction_file": out_path}
        except Exception as e:
            results[matchup_file] = {"status": "failed", "error": str(e)}
    # Event summary
    summary = {
        "event": event['event_name'],
        "date": event['date'],
        "venue": event['venue'],
        "results": results
    }
    save_json("C:/ai_risa_data/reports/boxing_o2_arena_2026_04_04_summary.json", summary)

if __name__ == "__main__":
    main()
