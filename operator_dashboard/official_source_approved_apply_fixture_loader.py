"""Official Source Approved Apply fixture loader/builder.

Loads fixture JSON scenario definitions from
tests/fixtures/official_source_approved_apply/scenarios/ and builds
runtime scenarios with injected tokens.

Rules:
- Never writes files.
- Never calls external lookup.
- Never persists consumed tokens.
- token_mode controls token injection strategy.
"""
from __future__ import annotations

import copy
import json
import os
from typing import NamedTuple

from operator_dashboard.official_source_approved_apply_token import (
    issue_official_source_approved_apply_token,
)

_FIXTURE_SCENARIOS_ROOT = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "tests",
        "fixtures",
        "official_source_approved_apply",
        "scenarios",
    )
)


class BuiltScenario(NamedTuple):
    scenario_id: str
    description: str
    token_mode: str
    request_payload: dict | None
    authoritative_preview_result: dict | None
    now_epoch: int
    consumed_token_ids: frozenset
    replayed_token_ids: frozenset
    expected: dict
    issued_token_id: str | None


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_scenario(fixture: dict) -> BuiltScenario:
    """Process a raw fixture dict into a BuiltScenario with token injected."""
    scenario_id = str(fixture.get("scenario_id") or "")
    description = str(fixture.get("description") or "")
    token_mode = str(fixture.get("token_mode") or "none")
    token_issue_epoch = int(fixture.get("token_issue_epoch") or 1700000000)
    token_ttl_seconds = int(fixture.get("token_ttl_seconds") or 120)
    now_epoch = int(fixture.get("now_epoch") or 1700000060)

    request_payload = copy.deepcopy(fixture.get("request_payload"))
    authoritative_preview_result = copy.deepcopy(
        fixture.get("authoritative_preview_result")
    )

    consumed_token_ids: frozenset = frozenset(
        fixture.get("consumed_token_ids_from_fixture") or []
    )
    replayed_token_ids: frozenset = frozenset(
        fixture.get("replayed_token_ids_from_fixture") or []
    )

    issued_token_id: str | None = None

    if token_mode in ("valid", "expired", "replayed", "consumed", "binding_mismatch"):
        if not isinstance(request_payload, dict):
            raise ValueError(
                f"Fixture '{scenario_id}': token_mode='{token_mode}' requires "
                "a non-null request_payload dict."
            )

        binding_for_token = fixture.get("token_binding_override") or request_payload.get(
            "approval_binding", {}
        )

        issued = issue_official_source_approved_apply_token(
            binding_for_token,
            now_epoch=token_issue_epoch,
            ttl_seconds=token_ttl_seconds,
        )

        if not issued.get("ok"):
            raise ValueError(
                f"Fixture '{scenario_id}': token issuance failed: "
                f"{issued.get('errors')}"
            )

        request_payload["approval_token"] = issued["token"]
        issued_token_id = str(issued["token_id"])

        if token_mode == "replayed":
            replayed_token_ids = frozenset(replayed_token_ids | {issued_token_id})
        elif token_mode == "consumed":
            consumed_token_ids = frozenset(consumed_token_ids | {issued_token_id})

    return BuiltScenario(
        scenario_id=scenario_id,
        description=description,
        token_mode=token_mode,
        request_payload=request_payload,
        authoritative_preview_result=authoritative_preview_result,
        now_epoch=now_epoch,
        consumed_token_ids=consumed_token_ids,
        replayed_token_ids=replayed_token_ids,
        expected=dict(fixture.get("expected") or {}),
        issued_token_id=issued_token_id,
    )


def load_scenario(scenario_id: str, *, base_dir: str | None = None) -> BuiltScenario:
    """Load and build a named scenario by searching the fixture tree."""
    root = base_dir or _FIXTURE_SCENARIOS_ROOT
    target = scenario_id + ".json"
    for dirpath, _dirs, filenames in os.walk(root):
        if target in filenames:
            fixture = _load_json(os.path.join(dirpath, target))
            return build_scenario(fixture)
    raise FileNotFoundError(
        f"Fixture scenario '{scenario_id}' not found under {root}"
    )


def load_all_scenarios(*, base_dir: str | None = None) -> list[BuiltScenario]:
    """Load and build every scenario JSON found in the fixture tree."""
    root = base_dir or _FIXTURE_SCENARIOS_ROOT
    scenarios: list[BuiltScenario] = []
    for dirpath, _dirs, filenames in os.walk(root):
        for filename in sorted(filenames):
            if filename.endswith(".json"):
                fixture = _load_json(os.path.join(dirpath, filename))
                scenarios.append(build_scenario(fixture))
    return scenarios


def load_scenarios_by_subdirectory(subdir: str, *, base_dir: str | None = None) -> list[BuiltScenario]:
    """Load all scenarios from a named subdirectory (e.g. 'deny', 'manual_review', 'placeholder')."""
    root = base_dir or _FIXTURE_SCENARIOS_ROOT
    target_dir = os.path.join(root, subdir)
    scenarios: list[BuiltScenario] = []
    if not os.path.isdir(target_dir):
        return scenarios
    for filename in sorted(os.listdir(target_dir)):
        if filename.endswith(".json"):
            fixture = _load_json(os.path.join(target_dir, filename))
            scenarios.append(build_scenario(fixture))
    return scenarios


__all__ = [
    "BuiltScenario",
    "build_scenario",
    "load_scenario",
    "load_all_scenarios",
    "load_scenarios_by_subdirectory",
]
