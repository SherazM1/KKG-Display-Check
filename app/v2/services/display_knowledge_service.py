"""Deterministic display knowledge lookup without inferred fallback facts."""

from app.v2.knowledge.display_profiles import DISPLAY_KNOWLEDGE_PROFILES
from app.v2.models import DisplayKnowledgeProfile, ResolvedDisplay


class DisplayKnowledgeError(LookupError):
    """No reference knowledge exists for the requested display identity."""


def resolve_display_knowledge(display: ResolvedDisplay) -> DisplayKnowledgeProfile:
    """Prefer baseline knowledge, then knowledge for the exact configuration."""
    for baseline_id in (display.baseline_id, None):
        for profile in DISPLAY_KNOWLEDGE_PROFILES:
            if (
                profile.family_id == display.family_id
                and profile.configuration_id == display.configuration_id
                and profile.baseline_id == baseline_id
            ):
                return profile

    raise DisplayKnowledgeError(
        f'No display knowledge profile exists for "{display.family_id}/'
        f'{display.configuration_id}/{display.baseline_id}"'
    )
