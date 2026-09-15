"""Deterministic estimating basis from project inputs and verified knowledge."""

from app.v2.models import (
    DisplayKnowledgeProfile,
    EstimateBasis,
    ProjectContext,
    ResolvedDisplay,
)


class EstimateBasisError(ValueError):
    """Display knowledge does not match the resolved display identity."""


def build_estimate_basis(
    project: ProjectContext,
    display: ResolvedDisplay,
    knowledge: DisplayKnowledgeProfile,
) -> EstimateBasis:
    """Carry direct facts forward without inferring estimating or pricing rules."""
    if knowledge.family_id != display.family_id:
        raise EstimateBasisError("Display knowledge family does not match resolved display.")
    if knowledge.configuration_id != display.configuration_id:
        raise EstimateBasisError(
            "Display knowledge configuration does not match resolved display."
        )
    if knowledge.baseline_id is not None and knowledge.baseline_id != display.baseline_id:
        raise EstimateBasisError(
            "Display knowledge baseline does not match resolved display."
        )

    contributing_rules = tuple(
        rule_id
        for rule_id, facts in (
            ("display_knowledge.structural_traits", knowledge.structural_traits),
            ("display_knowledge.known_materials", knowledge.known_materials),
            ("display_knowledge.production_notes", knowledge.production_notes),
            ("display_knowledge.known_unknowns", knowledge.known_unknowns),
        )
        if facts
    )
    # Foundational guardrail until verified PM review criteria are available.
    review_required = bool(knowledge.known_unknowns)
    review_reasons = ()
    if review_required:
        review_reasons = ("Display knowledge contains unresolved technical unknowns.",)
        contributing_rules += ("review.unknown_display_knowledge",)

    return EstimateBasis(
        family_id=display.family_id,
        configuration_id=display.configuration_id,
        baseline_id=display.baseline_id,
        footprint_id=display.footprint_id,
        quantity=project.quantity,
        print_type=project.print_type,
        shipping_packout=project.shipping_packout,
        width=display.width,
        height=display.height,
        depth=display.depth,
        units=display.units,
        structural_factors=knowledge.structural_traits,
        material_factors=knowledge.known_materials,
        print_factors=(),
        production_factors=knowledge.production_notes,
        assembly_factors=(),
        packout_factors=(),
        quantity_factors=(),
        assumptions=(),
        unknowns=knowledge.known_unknowns,
        risk_factors=(),
        review_required=review_required,
        review_reasons=review_reasons,
        contributing_rules=contributing_rules,
    )
