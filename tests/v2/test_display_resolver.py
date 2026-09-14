"""Tests for strict backend display resolution."""

from dataclasses import replace

import pytest

from app.v2 import display_registry
from app.v2.models import ProjectContext, ProjectDimensions, ResolvedDisplay
from app.v2.services.display_resolver import DisplayResolutionError, resolve_display


def test_valid_sidekick_uses_canonical_selection_and_project_dimensions() -> None:
    project = ProjectContext(dimensions=ProjectDimensions(21, 47, 13))

    assert resolve_display(project) == ResolvedDisplay(
        family_id="sidekick",
        configuration_id="hooks",
        baseline_id="24",
        footprint_id="sk-24-hooks",
        family_label="Sidekick",
        configuration_label="Hooks",
        baseline_label="24",
        width=21,
        height=47,
        depth=13,
        units="in",
    )


@pytest.mark.parametrize("family_id", ["foo", "", "Sidekick", " sidekick"])
def test_unknown_family_is_not_repaired(family_id: str) -> None:
    with pytest.raises(DisplayResolutionError) as error:
        resolve_display(ProjectContext(display_family=family_id))
    assert str(error.value) == f'Unknown display family: "{family_id}"'


def test_configuration_from_another_family_is_invalid() -> None:
    with pytest.raises(DisplayResolutionError) as error:
        resolve_display(ProjectContext(display_configuration="angled"))
    assert str(error.value) == (
        'Configuration "angled" is not valid for display family "sidekick"'
    )


def test_baseline_from_another_configuration_is_invalid() -> None:
    with pytest.raises(DisplayResolutionError) as error:
        resolve_display(ProjectContext(baseline_size="36x12x12"))
    assert str(error.value) == (
        'Baseline "36x12x12" is not valid for configuration "hooks"'
    )


@pytest.mark.parametrize("footprint_id", ["fp-36x12x12", "", "sk-24-hooks "])
def test_mismatched_footprint_is_not_repaired(footprint_id: str) -> None:
    with pytest.raises(DisplayResolutionError) as error:
        resolve_display(ProjectContext(footprint_id=footprint_id))
    assert str(error.value) == (
        f'Footprint "{footprint_id}" does not match canonical footprint "sk-24-hooks"'
    )


@pytest.mark.parametrize("footprint_id", ["", " "])
def test_canonical_baseline_requires_footprint(
    monkeypatch: pytest.MonkeyPatch, footprint_id: str
) -> None:
    family = display_registry.get_family("sidekick")
    assert family is not None
    configuration = family.configurations[0]
    baseline = replace(configuration.baselines[0], footprint_id=footprint_id)
    configuration = replace(configuration, baselines=(baseline,))
    family = replace(family, configurations=(configuration,))
    monkeypatch.setattr(display_registry, "DISPLAY_FAMILIES", (family,))

    with pytest.raises(DisplayResolutionError) as error:
        resolve_display(ProjectContext(footprint_id=footprint_id))
    assert str(error.value) == 'Baseline "24" has no canonical footprint'


@pytest.mark.parametrize("dimension", ["width", "height", "depth"])
@pytest.mark.parametrize("value", [None, 0, -1, float("nan")])
def test_dimensions_must_exist_and_be_positive(
    dimension: str, value: float | None
) -> None:
    project = ProjectContext()
    setattr(project.dimensions, dimension, value)

    with pytest.raises(DisplayResolutionError) as error:
        resolve_display(project)
    assert str(error.value) == f"{dimension.capitalize()} must be greater than zero"


def test_quarter_pallet_custom_uses_user_dimensions() -> None:
    project = ProjectContext(
        display_family="quarter_pallet",
        display_configuration="shroud",
        baseline_size="custom",
        footprint_id="custom",
        dimensions=ProjectDimensions(23.5, 51, 19),
    )

    assert resolve_display(project) == ResolvedDisplay(
        family_id="quarter_pallet",
        configuration_id="shroud",
        baseline_id="custom",
        footprint_id="custom",
        family_label="Quarter Pallet",
        configuration_label="Shroud",
        baseline_label="Custom",
        width=23.5,
        height=51,
        depth=19,
    )
