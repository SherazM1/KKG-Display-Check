"""Tests for Display Check v2 project readiness."""

from app.v2.models import ProjectContext, ProjectDimensions, is_project_ready


def test_project_ready_when_required_fields_are_valid() -> None:
    """A default project has all required fields."""
    assert is_project_ready(ProjectContext())


def test_project_not_ready_without_display_family() -> None:
    """Display family is required."""
    assert not is_project_ready(ProjectContext(display_family=""))


def test_project_not_ready_without_display_configuration() -> None:
    """Display configuration is required."""
    assert not is_project_ready(ProjectContext(display_configuration=""))


def test_project_not_ready_without_baseline_size() -> None:
    """Baseline size or footprint is required."""
    assert not is_project_ready(ProjectContext(baseline_size=""))


def test_project_not_ready_without_footprint_id() -> None:
    """Resolved footprint id is required."""
    assert not is_project_ready(ProjectContext(footprint_id=""))


def test_project_not_ready_when_quantity_is_less_than_one() -> None:
    """Quantity must be at least one."""
    assert not is_project_ready(ProjectContext(quantity=0))


def test_project_not_ready_without_print_type() -> None:
    """Print type is required."""
    assert not is_project_ready(ProjectContext(print_type=""))


def test_project_not_ready_without_shipping_packout() -> None:
    """Shipping / packout is required."""
    assert not is_project_ready(ProjectContext(shipping_packout=""))


def test_dimensions_are_optional_for_readiness() -> None:
    """Missing dimensions do not block assistant readiness."""
    project = ProjectContext(dimensions=ProjectDimensions())

    assert is_project_ready(project)


def test_reference_image_is_optional_for_readiness() -> None:
    """Missing reference image does not block assistant readiness."""
    project = ProjectContext(reference_image=None, reference_image_name=None)

    assert is_project_ready(project)
