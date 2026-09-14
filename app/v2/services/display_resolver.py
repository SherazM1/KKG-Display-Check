"""Strict, Streamlit-independent resolution of physical display selections."""

from app.v2.display_registry import get_baseline, get_configuration, get_family
from app.v2.models import ProjectContext, ResolvedDisplay


class DisplayResolutionError(ValueError):
    """A project cannot resolve to a valid canonical display."""


def _positive_dimension(value: float | None, label: str) -> float:
    if value is None or not value > 0:
        raise DisplayResolutionError(f"{label} must be greater than zero")
    return value


def resolve_display(project: ProjectContext) -> ResolvedDisplay:
    """Validate exact registry IDs and final project dimensions without fallback."""
    family = get_family(project.display_family)
    if family is None:
        raise DisplayResolutionError(f'Unknown display family: "{project.display_family}"')

    configuration = get_configuration(family, project.display_configuration)
    if configuration is None:
        raise DisplayResolutionError(
            f'Configuration "{project.display_configuration}" is not valid '
            f'for display family "{family.id}"'
        )

    baseline = get_baseline(configuration, project.baseline_size)
    if baseline is None:
        raise DisplayResolutionError(
            f'Baseline "{project.baseline_size}" is not valid '
            f'for configuration "{configuration.id}"'
        )
    if not baseline.footprint_id.strip():
        raise DisplayResolutionError(
            f'Baseline "{baseline.id}" has no canonical footprint'
        )
    if project.footprint_id != baseline.footprint_id:
        raise DisplayResolutionError(
            f'Footprint "{project.footprint_id}" does not match '
            f'canonical footprint "{baseline.footprint_id}"'
        )

    width = _positive_dimension(project.dimensions.width, "Width")
    height = _positive_dimension(project.dimensions.height, "Height")
    depth = _positive_dimension(project.dimensions.depth, "Depth")
    return ResolvedDisplay(
        family_id=family.id,
        configuration_id=configuration.id,
        baseline_id=baseline.id,
        footprint_id=baseline.footprint_id,
        family_label=family.label,
        configuration_label=configuration.label,
        baseline_label=baseline.label,
        width=width,
        height=height,
        depth=depth,
        units="in",
    )
