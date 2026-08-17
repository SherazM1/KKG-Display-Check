"""Tests for Display Check v2 domain and mock services."""

from app.v2.mock_data import BASE_TEMPLATE, STATIC_MOCKUP
from app.v2.models import ProjectContext, ProjectDimensions
from app.v2.services.estimate_service import EstimateService
from app.v2.services.visual_service import VisualService


def test_project_context_defaults() -> None:
    """ProjectContext exposes sensible default values."""
    project = ProjectContext()

    assert project.project_name == "Display Check Sample"
    assert project.display_type == "Sidekick"
    assert project.quantity == 500
    assert project.print_type == "Litho Laminate"
    assert project.shipping_packout == "Flat Pack"
    assert project.dimensions == ProjectDimensions(width=20, height=48, depth=12)


def test_estimate_service_reflects_context_and_program_range() -> None:
    """Mock estimate response uses display type and quantity consistently."""
    project = ProjectContext(
        display_type="Sidekick",
        quantity=500,
        dimensions=ProjectDimensions(width=20, height=48, depth=12),
    )
    response = EstimateService().analyze(project)

    assert response.details.display_type == "Sidekick"
    assert response.program_price_range.low == response.unit_price_range.low * 500
    assert response.program_price_range.high == response.unit_price_range.high * 500


def test_visual_service_returns_sidekick_template() -> None:
    """Mock visual response maps Sidekick to the static Sidekick template."""
    response = VisualService().prepare(ProjectContext(display_type="Sidekick"))

    assert response.display_type == "Sidekick"
    assert BASE_TEMPLATE.name == "base_sidekick.png"
    assert response.base_template == str(BASE_TEMPLATE)
    assert len(response.palette) == 4


def test_static_mockup_uses_new_sidekick_reference() -> None:
    """Mock preliminary output uses the canonical static Sidekick visual."""
    assert STATIC_MOCKUP.name == "staticreference_sk.png"
