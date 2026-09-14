"""Tests for strict reference knowledge identity and lookup precedence."""

from dataclasses import replace

import pytest

from app.v2.models import ProjectContext, ResolvedDisplay
from app.v2.services import display_knowledge_service
from app.v2.services.display_knowledge_service import (
    DisplayKnowledgeError,
    resolve_display_knowledge,
)
from app.v2.services.display_resolver import resolve_display


@pytest.fixture
def hooks_display() -> ResolvedDisplay:
    return resolve_display(ProjectContext())


def test_hooks_resolves_configuration_knowledge(hooks_display: ResolvedDisplay) -> None:
    profile = resolve_display_knowledge(hooks_display)

    assert profile.profile_id == "sidekick/hooks"
    assert profile.family_id == "sidekick"
    assert profile.configuration_id == "hooks"
    assert profile.baseline_id is None
    assert "Baseline height and depth are not verified." in profile.known_unknowns
    assert "Materials and board grade are not verified." in profile.known_unknowns
    assert profile.sources
    assert profile.structural_traits == ()
    assert profile.visible_components == ()
    assert profile.hidden_support_components == ()
    assert profile.known_materials == ()


def test_hooks_48_shares_configuration_profile(hooks_display: ResolvedDisplay) -> None:
    display_48 = resolve_display(
        ProjectContext(baseline_size="48", footprint_id="sk-48-hooks")
    )

    assert resolve_display_knowledge(display_48) is resolve_display_knowledge(hooks_display)


def test_unseeded_configuration_fails() -> None:
    display = resolve_display(
        ProjectContext(
            display_configuration="shelves_built", footprint_id="sk-24-shelves-built"
        )
    )

    with pytest.raises(DisplayKnowledgeError) as error:
        resolve_display_knowledge(display)
    assert str(error.value) == (
        'No display knowledge profile exists for "sidekick/shelves_built/24"'
    )


def test_other_family_cannot_reuse_hooks_knowledge(hooks_display: ResolvedDisplay) -> None:
    display = replace(hooks_display, family_id="unknown")

    with pytest.raises(DisplayKnowledgeError) as error:
        resolve_display_knowledge(display)
    assert str(error.value) == (
        'No display knowledge profile exists for "unknown/hooks/24"'
    )


def test_baseline_profile_takes_precedence(
    monkeypatch: pytest.MonkeyPatch, hooks_display: ResolvedDisplay
) -> None:
    configuration_profile = resolve_display_knowledge(hooks_display)
    baseline_profile = replace(
        configuration_profile, profile_id="test/hooks/24", baseline_id="24"
    )
    monkeypatch.setattr(
        display_knowledge_service,
        "DISPLAY_KNOWLEDGE_PROFILES",
        (configuration_profile, baseline_profile),
    )

    assert resolve_display_knowledge(hooks_display) is baseline_profile
    display_48 = resolve_display(
        ProjectContext(baseline_size="48", footprint_id="sk-48-hooks")
    )
    assert resolve_display_knowledge(display_48) is configuration_profile


def test_other_baseline_knowledge_is_not_substituted(
    monkeypatch: pytest.MonkeyPatch, hooks_display: ResolvedDisplay
) -> None:
    profile = replace(
        resolve_display_knowledge(hooks_display),
        profile_id="test/hooks/48",
        baseline_id="48",
    )
    monkeypatch.setattr(
        display_knowledge_service, "DISPLAY_KNOWLEDGE_PROFILES", (profile,)
    )

    with pytest.raises(DisplayKnowledgeError) as error:
        resolve_display_knowledge(hooks_display)
    assert str(error.value) == (
        'No display knowledge profile exists for "sidekick/hooks/24"'
    )
