# accuracy_ledger_schema.py
"""
Defines the canonical schema for the AI-RISA accuracy ledger.
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AccuracyLedgerRecord(BaseModel):
    fight_id: str
    event_date: str  # ISO date (YYYY-MM-DD)
    fighter_a: str
    fighter_b: str
    predicted_winner: str
    predicted_method: str
    predicted_round: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    actual_winner: str
    actual_method: str
    actual_round: str
    hit_winner: bool
    hit_method: bool
    round_error: Optional[int] = None
    confidence_bucket: str
    # Optionally: add model_version, calibration_version, etc.
    prediction_id: Optional[str] = None
    model_version: Optional[str] = None
    calibration_version: Optional[str] = None
    prediction_timestamp: Optional[datetime] = None
