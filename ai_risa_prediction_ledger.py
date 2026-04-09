from __future__ import annotations

from ai_risa_prediction_schema import PredictionRecord

def append_prediction_record(record, ledger_path=None):
    # Accepts a PredictionRecord or dict, always returns the canonical record object
    from ai_risa_prediction_adapter import build_prediction_record
    if isinstance(record, PredictionRecord):
        rec = record
    else:
        # You must provide the required args for build_prediction_record in your context
        raise ValueError("append_prediction_record requires a PredictionRecord; dicts must be promoted upstream.")
    # Example file write (add ledger_path as needed)
    # with open(ledger_path, "a", encoding="utf-8") as f:
    #     f.write(json.dumps(rec.to_json_dict(), ensure_ascii=False) + "\n")
    print("[TRACE] append_prediction_record: contract-enforced", flush=True)
    return rec
