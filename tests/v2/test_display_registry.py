"""Tests for Display Check v2 display selection registry."""

from app.v2.display_registry import resolve_display_selection


def test_sidekick_configuration_change_preserves_shared_size() -> None:
    """Sidekick 24 remains selected when moving between 24/48 configurations."""
    selection = resolve_display_selection("sidekick", "shelves_built", "24")

    assert selection.family.id == "sidekick"
    assert selection.configuration.id == "shelves_built"
    assert selection.baseline.id == "24"
    assert selection.baseline.footprint_id == "sk-24-shelves-built"
    assert selection.baseline.asset_path is not None
    assert selection.baseline.asset_path.name == "sidekickshelves24.png"


def test_family_change_resets_stale_configuration_and_size() -> None:
    """A prior Sidekick selection resolves to valid PDQ defaults when family changes."""
    selection = resolve_display_selection("pdq", "shelves_rolled", "48")

    assert selection.family.id == "pdq"
    assert selection.configuration.id == "angled"
    assert selection.baseline.id == "36x12x12"
    assert selection.baseline.footprint_id == "fp-36x12x12"


def test_pdq_footprints_include_full_dimensions() -> None:
    """PDQ footprints carry explicit W/H/D values from the v1 catalog."""
    selection = resolve_display_selection("pdq", "clipped", "48x17x12")

    assert selection.baseline.width == 48
    assert selection.baseline.height == 12
    assert selection.baseline.depth == 17


def test_quarter_pallet_resolves_to_custom_baseline() -> None:
    """Quarter pallet configurations currently expose only Custom as baseline."""
    selection = resolve_display_selection("quarter_pallet", "dump_bin", None)

    assert selection.family.id == "quarter_pallet"
    assert selection.configuration.id == "dump_bin"
    assert selection.baseline.id == "custom"
