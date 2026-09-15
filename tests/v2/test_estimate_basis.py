"""Tests for conservative estimating facts, identity checks, and traceability."""

from dataclasses import FrozenInstanceError, replace

import pytest

from app.v2.models import DisplayKnowledgeProfile, EstimateBasis, ProjectContext
from app.v2.services.display_knowledge_service import resolve_display_knowledge
from app.v2.services.display_resolver import resolve_display
from app.v2.services.estimate_basis_service import EstimateBasisError, build_estimate_basis


@pytest.fixture
def knowledge() -> DisplayKnowledgeProfile:
    # Synthetic facts exercise mapping; they do not extend verified registry data.
    return DisplayKnowledgeProfile(
        profile_id="test/hooks",
        family_id="sidekick",
        configuration_id="hooks",
        baseline_id=None,
        structural_traits=(),
        visible_components=("Test visible component",),
        hidden_support_components=("Test hidden component",),
        known_materials=(),
        production_notes=(),
        known_unknowns=(),
        sources=("Test fixture",),
    )


def test_builds_basis_from_resolved_identity_and_project_inputs(knowledge) -> None:
    project = ProjectContext(
        quantity=1200, print_type="Digital", shipping_packout="Assembled"
    )
    display = replace(resolve_display(project), width=21.5, height=47.0, depth=13.0)
    basis = build_estimate_basis(project, display, knowledge)

    assert isinstance(basis, EstimateBasis)
    assert (basis.family_id, basis.configuration_id, basis.baseline_id, basis.footprint_id) == (
        "sidekick", "hooks", "24", "sk-24-hooks"
    )
    assert (basis.quantity, basis.print_type, basis.shipping_packout) == (
        1200, "Digital", "Assembled"
    )
    assert (basis.width, basis.height, basis.depth, basis.units) == (21.5, 47.0, 13.0, "in")
    assert basis == build_estimate_basis(project, display, knowledge)


@pytest.mark.parametrize(
    ("source", "target"),
    [
        ("structural_traits", "structural_factors"),
        ("known_materials", "material_factors"),
        ("production_notes", "production_factors"),
        ("known_unknowns", "unknowns"),
    ],
)
def test_direct_mapping_and_only_contributing_rules(knowledge, source, target) -> None:
    facts = ("Test fact one", "Test fact two")
    knowledge = replace(knowledge, **{source: facts})
    project = ProjectContext()

    basis = build_estimate_basis(project, resolve_display(project), knowledge)

    assert getattr(basis, target) == facts
    expected_rules = (f"display_knowledge.{source}",)
    if source == "known_unknowns":
        expected_rules += ("review.unknown_display_knowledge",)
    assert basis.contributing_rules == expected_rules


def test_unknowns_require_review() -> None:
    project = ProjectContext()
    display = resolve_display(project)
    knowledge = resolve_display_knowledge(display)

    basis = build_estimate_basis(project, display, knowledge)

    assert basis.unknowns == knowledge.known_unknowns
    assert basis.review_required is True
    assert basis.review_reasons == (
        "Display knowledge contains unresolved technical unknowns.",
    )
    assert basis.assumptions == ()


def test_no_facts_produces_no_review_or_inferred_factors(knowledge) -> None:
    project = ProjectContext()
    basis = build_estimate_basis(project, resolve_display(project), knowledge)

    assert basis.review_required is False
    assert basis.review_reasons == ()
    assert basis.contributing_rules == ()
    for name in (
        "structural_factors", "material_factors", "print_factors",
        "production_factors", "assembly_factors", "packout_factors",
        "quantity_factors", "risk_factors", "unknowns", "assumptions",
    ):
        assert getattr(basis, name) == ()
    with pytest.raises(FrozenInstanceError):
        basis.quantity = 1


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("family_id", "other", "Display knowledge family does not match resolved display."),
        (
            "configuration_id", "other",
            "Display knowledge configuration does not match resolved display.",
        ),
        ("baseline_id", "48", "Display knowledge baseline does not match resolved display."),
    ],
)
def test_mismatched_knowledge_raises(knowledge, field, value, message) -> None:
    project = ProjectContext()
    with pytest.raises(EstimateBasisError) as error:
        build_estimate_basis(
            project, resolve_display(project), replace(knowledge, **{field: value})
        )
    assert str(error.value) == message


@pytest.mark.parametrize("baseline_id", [None, "24"])
def test_matching_configuration_or_baseline_knowledge_is_valid(knowledge, baseline_id) -> None:
    project = ProjectContext()
    basis = build_estimate_basis(
        project, resolve_display(project), replace(knowledge, baseline_id=baseline_id)
    )
    assert basis.baseline_id == "24"


def test_all_contributing_rules_have_stable_order(knowledge) -> None:
    project = ProjectContext()
    knowledge = replace(
        knowledge,
        structural_traits=("Test structure",),
        known_materials=("Test material",),
        production_notes=("Test production note",),
        known_unknowns=("Test unknown",),
    )

    basis = build_estimate_basis(project, resolve_display(project), knowledge)

    assert basis.contributing_rules == (
        "display_knowledge.structural_traits",
        "display_knowledge.known_materials",
        "display_knowledge.production_notes",
        "display_knowledge.known_unknowns",
        "review.unknown_display_knowledge",
    )
