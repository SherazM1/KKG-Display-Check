"""Conservative display reference data; gaps must not be filled by inference."""

from app.v2.models import DisplayKnowledgeProfile


DISPLAY_KNOWLEDGE_PROFILES = (
    DisplayKnowledgeProfile(
        profile_id="sidekick/hooks",
        family_id="sidekick",
        configuration_id="hooks",
        baseline_id=None,
        structural_traits=(),
        visible_components=(),
        hidden_support_components=(),
        known_materials=(),
        production_notes=(
            "Sidekick Hooks has 24-inch and 48-inch baseline width options.",
            "The legacy catalog records variant-to-part relationships for both Hooks baselines; "
            "these relationships have not been classified as v2 component knowledge.",
        ),
        known_unknowns=(
            "Baseline height and depth are not verified.",
            "Structural traits and visible/hidden support component classifications are not verified.",
            "Materials and board grade are not verified.",
            "Header construction, glue requirements, load capacity, reinforcement, "
            "and assembly labor are not verified.",
        ),
        sources=(
            "app/v2/display_registry.py: DISPLAY_FAMILIES sidekick/hooks baselines 24 and 48",
            "data/catalog/sidekick.json: controls[footprint].options "
            "sk-24-hooks and sk-48-hooks (dims.width_in)",
            "data/catalog/sidekick.json: rules.resolve_footprint_base.map "
            "(sk-24-hooks -> KK260014-01; sk-48-hooks -> KK260015-01)",
        ),
    ),
)
