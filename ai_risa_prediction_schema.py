from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class WorkflowType(str, Enum):
    SINGLE_FIGHT = "single_fight"
    HEAD_TO_HEAD = "head_to_head"
    EVENT_CARD = "event_card"


class PredictionStatus(str, Enum):
    PREDICTED = "predicted"
    RECONCILED = "reconciled"
    APPLIED = "applied"


class InputConfig(BaseModel):
    stoppage_sensitivity: float = 1.0
    simulation_count: int = 1000
    source_matchup_file: str | None = None
    extras: dict[str, Any] = Field(default_factory=dict)


class ProfileSources(BaseModel):
    fighter_a_profile_path: str
    fighter_b_profile_path: str


class ProfileHashes(BaseModel):
    fighter_a_hash: str | None = None
    fighter_b_hash: str | None = None


class PredictionRecord(BaseModel):
    signal_gap: float | None = None
    stoppage_propensity: float | None = None
    round_finish_tendency: float | None = None
    schema_version: str = "prediction_record_v1"
    prediction_id: str
    prediction_family_id: str | None = None  # For grouping snapshots by matchup, backward compatible
    matchup_id: str
    workflow_type: WorkflowType
    prediction_timestamp: datetime

    fighter_a_id: str
    fighter_b_id: str

    predicted_winner_id: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    method: str
    round: str

    model_version: str
    calibration_version: str
    fighter_prior_version: str

    input_config: InputConfig
    profile_sources: ProfileSources
    profile_hashes: ProfileHashes = Field(default_factory=ProfileHashes)

    debug_metrics: dict[str, Any] = Field(default_factory=dict)
    artifact_paths: list[str] = Field(default_factory=list)

    status: PredictionStatus = PredictionStatus.PREDICTED

    @field_validator("artifact_paths", mode="before")
    @classmethod
    def ensure_artifact_paths_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v) for v in value]
        if isinstance(value, str):
            return [value]
        raise TypeError("artifact_paths must be a list of strings")

    @model_validator(mode="after")
    def validate_winner(self) -> "PredictionRecord":
        valid_ids = {self.fighter_a_id, self.fighter_b_id}
        if self.predicted_winner_id not in valid_ids:
            raise ValueError(
                f"predicted_winner_id must be one of fighter_a_id/fighter_b_id, got {self.predicted_winner_id}"
            )
        return self

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_json_file(cls, path: str | Path) -> "PredictionRecord":
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))
