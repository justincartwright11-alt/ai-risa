"""
Premium Report Factory global engine-pack betting market scaffold contracts.

Defines contract-only structures for Button 2 betting market intelligence.
No live odds fetching, no betting automation, and no runtime route wiring.
"""

from dataclasses import dataclass


ODDS_INGESTION = "betting.odds_ingestion"
IMPLIED_PROBABILITY = "betting.implied_probability"
FAIR_PRICE = "betting.fair_price"
MARKET_EDGE = "betting.market_edge"
PROP_MARKET = "betting.prop_market"
VOLATILITY_GRADE = "betting.volatility_grade"
PASS_NO_BET = "betting.pass_no_bet"
BETTING_RISK_DISCLAIMER = "betting.risk_disclaimer"

BETTING_ENGINE_IDS = (
    ODDS_INGESTION,
    IMPLIED_PROBABILITY,
    FAIR_PRICE,
    MARKET_EDGE,
    PROP_MARKET,
    VOLATILITY_GRADE,
    PASS_NO_BET,
    BETTING_RISK_DISCLAIMER,
)


@dataclass(frozen=True)
class BettingOutputContract:
    """Contract metadata for one betting market scaffold output."""

    engine_id: str
    output_key: str
    required: bool


def build_betting_market_contracts() -> dict[str, BettingOutputContract]:
    """Return contract definitions for Button 2 betting scaffold outputs."""

    return {
        ODDS_INGESTION: BettingOutputContract(ODDS_INGESTION, "odds_snapshot", True),
        IMPLIED_PROBABILITY: BettingOutputContract(IMPLIED_PROBABILITY, "implied_probability", True),
        FAIR_PRICE: BettingOutputContract(FAIR_PRICE, "fair_price", True),
        MARKET_EDGE: BettingOutputContract(MARKET_EDGE, "market_edge", True),
        PROP_MARKET: BettingOutputContract(PROP_MARKET, "prop_market", False),
        VOLATILITY_GRADE: BettingOutputContract(VOLATILITY_GRADE, "volatility_grade", True),
        PASS_NO_BET: BettingOutputContract(PASS_NO_BET, "pass_no_bet_condition", True),
        BETTING_RISK_DISCLAIMER: BettingOutputContract(BETTING_RISK_DISCLAIMER, "betting_risk_disclaimer", True),
    }


def validate_betting_outputs(
    engine_outputs: dict,
    contracts: dict[str, BettingOutputContract] | None = None,
) -> dict:
    """Validate contract presence and non-empty payloads for required outputs."""

    score_contracts = contracts or build_betting_market_contracts()
    missing_required_engines = []
    missing_required_output_values = []
    unknown_engines = []

    for engine_id, contract in score_contracts.items():
        if contract.required and engine_id not in engine_outputs:
            missing_required_engines.append(engine_id)

    for engine_id, output_payload in engine_outputs.items():
        contract = score_contracts.get(engine_id)
        if contract is None:
            unknown_engines.append(engine_id)
            continue

        if not contract.required:
            continue

        value = output_payload.get(contract.output_key) if isinstance(output_payload, dict) else None
        if isinstance(value, str):
            if not value.strip():
                missing_required_output_values.append(contract.output_key)
        elif value is None:
            missing_required_output_values.append(contract.output_key)

    ok = not missing_required_engines and not missing_required_output_values and not unknown_engines
    return {
        "ok": ok,
        "missing_required_engines": sorted(missing_required_engines),
        "missing_required_output_values": sorted(missing_required_output_values),
        "unknown_engines": sorted(unknown_engines),
    }


def evaluate_betting_output_gate(
    engine_outputs: dict,
    contracts: dict[str, BettingOutputContract] | None = None,
) -> dict:
    """
    Evaluate betting market scaffold gate for downstream customer-ready eligibility.

    This is contract-level gating only, not a live recommendation engine.
    """

    validation = validate_betting_outputs(engine_outputs, contracts)
    if validation["ok"]:
        return {
            "betting_gate_ready": True,
            "reason_code": "required_betting_contract_outputs_present",
            "validation": validation,
        }

    return {
        "betting_gate_ready": False,
        "reason_code": "missing_required_betting_contract_outputs",
        "validation": validation,
    }
