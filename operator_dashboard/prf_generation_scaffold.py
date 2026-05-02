"""
Premium Report Factory global engine-pack generation scaffold contracts.

Defines contract-only structures for Button 2 generation outputs.
No live PDF/report behavior changes or runtime route wiring.
"""

from dataclasses import dataclass


PREMIUM_PDF_GENERATION = "generation.premium_pdf"
EVENT_CARD_REPORT_PACK = "generation.event_card_pack"
SINGLE_MATCHUP_REPORT = "generation.single_matchup"
FIGHTER_PROFILE = "generation.fighter_profile"
BETTING_ANALYST_BRIEF = "generation.betting_analyst_brief"
BROADCAST_ANALYST_PACK = "generation.broadcast_analyst_pack"
COACH_GYM_SCOUTING_REPORT = "generation.coach_gym_scouting"
PROMOTER_MANAGER_DECISION_BRIEF = "generation.promoter_manager_decision_brief"
VISUAL_GENERATION = "generation.visual_generation"
CUSTOMER_READY_QA = "generation.customer_ready_qa"
DRAFT_WATERMARK = "generation.draft_watermark"
EXPORT_PROOF = "generation.download_export_proof"

GENERATION_ENGINE_IDS = (
    PREMIUM_PDF_GENERATION,
    EVENT_CARD_REPORT_PACK,
    SINGLE_MATCHUP_REPORT,
    FIGHTER_PROFILE,
    BETTING_ANALYST_BRIEF,
    BROADCAST_ANALYST_PACK,
    COACH_GYM_SCOUTING_REPORT,
    PROMOTER_MANAGER_DECISION_BRIEF,
    VISUAL_GENERATION,
    CUSTOMER_READY_QA,
    DRAFT_WATERMARK,
    EXPORT_PROOF,
)


@dataclass(frozen=True)
class GenerationOutputContract:
    """Contract metadata for one generation scaffold output."""

    engine_id: str
    output_key: str
    required: bool


def build_generation_contracts() -> dict[str, GenerationOutputContract]:
    """Return generation scaffold contracts for Button 2 outputs."""

    return {
        PREMIUM_PDF_GENERATION: GenerationOutputContract(PREMIUM_PDF_GENERATION, "premium_pdf_artifact", True),
        EVENT_CARD_REPORT_PACK: GenerationOutputContract(EVENT_CARD_REPORT_PACK, "event_card_pack_artifact", False),
        SINGLE_MATCHUP_REPORT: GenerationOutputContract(SINGLE_MATCHUP_REPORT, "single_matchup_report_artifact", True),
        FIGHTER_PROFILE: GenerationOutputContract(FIGHTER_PROFILE, "fighter_profile_artifact", False),
        BETTING_ANALYST_BRIEF: GenerationOutputContract(BETTING_ANALYST_BRIEF, "betting_analyst_brief_artifact", False),
        BROADCAST_ANALYST_PACK: GenerationOutputContract(BROADCAST_ANALYST_PACK, "broadcast_analyst_pack_artifact", False),
        COACH_GYM_SCOUTING_REPORT: GenerationOutputContract(COACH_GYM_SCOUTING_REPORT, "coach_gym_scouting_report_artifact", False),
        PROMOTER_MANAGER_DECISION_BRIEF: GenerationOutputContract(PROMOTER_MANAGER_DECISION_BRIEF, "promoter_manager_decision_brief_artifact", False),
        VISUAL_GENERATION: GenerationOutputContract(VISUAL_GENERATION, "visual_generation_bundle", False),
        CUSTOMER_READY_QA: GenerationOutputContract(CUSTOMER_READY_QA, "customer_ready_qa_result", True),
        DRAFT_WATERMARK: GenerationOutputContract(DRAFT_WATERMARK, "draft_watermark_result", True),
        EXPORT_PROOF: GenerationOutputContract(EXPORT_PROOF, "export_proof_record", True),
    }


def _is_present(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def validate_generation_outputs(
    engine_outputs: dict,
    contracts: dict[str, GenerationOutputContract] | None = None,
) -> dict:
    """Validate contract presence and non-empty output values for required engines."""

    output_contracts = contracts or build_generation_contracts()
    missing_required_engines = []
    missing_required_output_values = []
    unknown_engines = []

    for engine_id, contract in output_contracts.items():
        if contract.required and engine_id not in engine_outputs:
            missing_required_engines.append(engine_id)

    for engine_id, payload in engine_outputs.items():
        contract = output_contracts.get(engine_id)
        if contract is None:
            unknown_engines.append(engine_id)
            continue
        if not contract.required:
            continue
        output_value = payload.get(contract.output_key) if isinstance(payload, dict) else None
        if not _is_present(output_value):
            missing_required_output_values.append(contract.output_key)

    ok = not missing_required_engines and not missing_required_output_values and not unknown_engines
    return {
        "ok": ok,
        "missing_required_engines": sorted(missing_required_engines),
        "missing_required_output_values": sorted(missing_required_output_values),
        "unknown_engines": sorted(unknown_engines),
    }


def evaluate_generation_gate(
    engine_outputs: dict,
    allow_draft: bool,
    contracts: dict[str, GenerationOutputContract] | None = None,
) -> dict:
    """
    Evaluate generation scaffold gate state for customer-ready eligibility.

    Contract-level gate only; does not execute live generation or export.
    """

    validation = validate_generation_outputs(engine_outputs, contracts)
    if not validation["ok"]:
        if allow_draft:
            return {
                "generation_gate_ready": False,
                "report_quality_status": "draft_only",
                "reason_code": "generation_contract_outputs_missing_draft_mode",
                "validation": validation,
            }
        return {
            "generation_gate_ready": False,
            "report_quality_status": "blocked_missing_analysis",
            "reason_code": "generation_contract_outputs_missing",
            "validation": validation,
        }

    # Require explicit QA pass and export proof signals for customer-ready gate.
    qa_payload = engine_outputs.get(CUSTOMER_READY_QA) or {}
    export_payload = engine_outputs.get(EXPORT_PROOF) or {}
    qa_passed = bool(qa_payload.get("customer_ready_qa_result") == "pass")
    export_verified = bool(export_payload.get("export_proof_record"))

    if qa_passed and export_verified:
        return {
            "generation_gate_ready": True,
            "report_quality_status": "customer_ready",
            "reason_code": "generation_contracts_validated",
            "validation": validation,
        }

    if allow_draft:
        return {
            "generation_gate_ready": False,
            "report_quality_status": "draft_only",
            "reason_code": "qa_or_export_proof_not_customer_ready",
            "validation": validation,
        }

    return {
        "generation_gate_ready": False,
        "report_quality_status": "blocked_missing_analysis",
        "reason_code": "qa_or_export_proof_not_customer_ready",
        "validation": validation,
    }
