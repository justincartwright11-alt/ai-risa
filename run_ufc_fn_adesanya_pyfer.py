from __future__ import annotations

def engine_adapter(fight, requested_total_sims=1, confidence_scale=1.0):
    # Minimal stub: returns required keys for downstream logic
    return {
        "matchup_id": fight.get("matchup_id", "fighter_israel_adesanya_vs_fighter_joe_pyfer"),
        "fighter_a_id": fight.get("fighter_a_id", "fighter_israel_adesanya"),
        "fighter_b_id": fight.get("fighter_b_id", "fighter_joe_pyfer"),
        "predicted_winner_id": "fighter_joe_pyfer",
        "confidence": 0.5,
        "method": "Decision",
        "round": "full",
        "debug_metrics": {},
    }

def load_fighter_profile(name):
    # Minimal stub: returns a dict with a profile_path
    return {"profile_path": f"C:/Users/jusin/ai_risa_data/fighters/{name}.json"}

ID_TO_NAME = {
    "fighter_israel_adesanya": "Israel Adesanya",
    "fighter_joe_pyfer": "Joe Pyfer",
}
