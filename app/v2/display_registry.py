"""Normalized display selection registry for Display Check v2."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BaselineOption:
    """Selectable baseline size or footprint for a display configuration."""

    id: str
    label: str
    footprint_id: str
    width: float | None = None
    height: float | None = None
    depth: float | None = None
    units: str = "in"
    asset_path: Path | None = None


@dataclass(frozen=True)
class DisplayConfiguration:
    """Display subtype under a family."""

    id: str
    label: str
    legacy_id: str
    asset_path: Path | None
    baselines: tuple[BaselineOption, ...]


@dataclass(frozen=True)
class DisplayFamily:
    """Top-level display family."""

    id: str
    label: str
    configurations: tuple[DisplayConfiguration, ...]


@dataclass(frozen=True)
class DisplaySelection:
    """Resolved family/configuration/baseline tuple."""

    family: DisplayFamily
    configuration: DisplayConfiguration
    baseline: BaselineOption


PDQ_FOOTPRINTS = (
    BaselineOption("36x12x12", "36 x 12 x 12", "fp-36x12x12", width=36, height=12, depth=12),
    BaselineOption("36x17x12", "36 x 17 x 12", "fp-36x17x12", width=36, height=12, depth=17),
    BaselineOption("48x12x12", "48 x 12 x 12", "fp-48x12x12", width=48, height=12, depth=12),
    BaselineOption("48x17x12", "48 x 17 x 12", "fp-48x17x12", width=48, height=12, depth=17),
)

HALF_PALLET_FOOTPRINT = (
    BaselineOption("24x48", "24 x 48", "fp-24x48"),
)

CUSTOM_FOOTPRINT = (
    BaselineOption("custom", "Custom", "custom"),
)

DISPLAY_FAMILIES = (
    DisplayFamily(
        id="sidekick",
        label="Sidekick",
        configurations=(
            DisplayConfiguration(
                id="hooks",
                label="Hooks",
                legacy_id="sidekick/hooks",
                asset_path=Path("assets/references/sidekick/sidekickpeg24.png"),
                baselines=(
                    BaselineOption(
                        "24",
                        "24",
                        "sk-24-hooks",
                        width=24,
                        asset_path=Path("assets/references/sidekick/sidekickpeg24.png"),
                    ),
                    BaselineOption(
                        "48",
                        "48",
                        "sk-48-hooks",
                        width=48,
                        asset_path=Path("assets/references/sidekick/sidekickpeg48.png"),
                    ),
                ),
            ),
            DisplayConfiguration(
                id="shelves_rolled",
                label="Shelves - Rolled Sides",
                legacy_id="sidekick/shelves_rolled",
                asset_path=Path("assets/references/sidekick/sidekickshelves24.png"),
                baselines=(
                    BaselineOption(
                        "24",
                        "24",
                        "sk-24-shelves-rolled",
                        width=24,
                        asset_path=Path("assets/references/sidekick/sidekickshelves24.png"),
                    ),
                    BaselineOption(
                        "48",
                        "48",
                        "sk-48-shelves-rolled",
                        width=48,
                        asset_path=Path("assets/references/sidekick/sidekickshelves48.png"),
                    ),
                ),
            ),
            DisplayConfiguration(
                id="shelves_built",
                label="Shelves - Built-in",
                legacy_id="sidekick/shelves_built",
                asset_path=Path("assets/references/sidekick/sidekickshelves24.png"),
                baselines=(
                    BaselineOption(
                        "24",
                        "24",
                        "sk-24-shelves-built",
                        width=24,
                        asset_path=Path("assets/references/sidekick/sidekickshelves24.png"),
                    ),
                    BaselineOption(
                        "48",
                        "48",
                        "sk-48-shelves-built",
                        width=48,
                        asset_path=Path("assets/references/sidekick/sidekickshelves48.png"),
                    ),
                ),
            ),
        ),
    ),
    DisplayFamily(
        id="pdq",
        label="PDQ",
        configurations=(
            DisplayConfiguration(
                id="angled",
                label="Angled",
                legacy_id="pdq/digital_pdq_tray",
                asset_path=Path("assets/references/pdq/digital_pdq_tray.png"),
                baselines=PDQ_FOOTPRINTS,
            ),
            DisplayConfiguration(
                id="clipped",
                label="Clipped",
                legacy_id="pdq/clipped_pdq_tray",
                asset_path=Path("assets/references/pdq/clipped_pdq_tray.png"),
                baselines=PDQ_FOOTPRINTS,
            ),
            DisplayConfiguration(
                id="square",
                label="Square",
                legacy_id="pdq/square_pdq_tray",
                asset_path=Path("assets/references/pdq/square_pdq_tray.png"),
                baselines=PDQ_FOOTPRINTS,
            ),
            DisplayConfiguration(
                id="standard",
                label="Standard",
                legacy_id="pdq/standardclub_pdq_tray",
                asset_path=Path("assets/references/pdq/standardclub_pdq_tray.png"),
                baselines=PDQ_FOOTPRINTS,
            ),
        ),
    ),
    DisplayFamily(
        id="half_pallet",
        label="Half Pallet",
        configurations=(
            DisplayConfiguration(
                id="front_faced",
                label="Front-Faced",
                legacy_id="halfpallet/frontfaced_hp",
                asset_path=Path("assets/references/halfpallet/frontfaced_hp.png"),
                baselines=HALF_PALLET_FOOTPRINT,
            ),
            DisplayConfiguration(
                id="three_sided",
                label="Three-Sided",
                legacy_id="halfpallet/threesided_hp",
                asset_path=Path("assets/references/halfpallet/threesided_hp.png"),
                baselines=HALF_PALLET_FOOTPRINT,
            ),
            DisplayConfiguration(
                id="dump_bin",
                label="Dump Bin",
                legacy_id="halfpallet/dump_bin",
                asset_path=Path("assets/references/dumpbin/dump_bin.png"),
                baselines=HALF_PALLET_FOOTPRINT,
            ),
        ),
    ),
    DisplayFamily(
        id="quarter_pallet",
        label="Quarter Pallet",
        configurations=(
            DisplayConfiguration(
                id="shroud",
                label="Shroud",
                legacy_id="quarterpallet/qp-shroud",
                asset_path=Path("assets/references/quarterpallet/qp-shroud.png"),
                baselines=CUSTOM_FOOTPRINT,
            ),
            DisplayConfiguration(
                id="shelved",
                label="Shelved",
                legacy_id="quarterpallet/qp-shelved",
                asset_path=Path("assets/references/quarterpallet/qp-shelved.png"),
                baselines=CUSTOM_FOOTPRINT,
            ),
            DisplayConfiguration(
                id="stacked",
                label="Stacked",
                legacy_id="quarterpallet/qp-stacked-trays",
                asset_path=Path("assets/references/quarterpallet/qp-stacked-trays.png"),
                baselines=CUSTOM_FOOTPRINT,
            ),
            DisplayConfiguration(
                id="dump_bin",
                label="Dump Bin",
                legacy_id="quarterpallet/qp-dumpbin",
                asset_path=Path("assets/references/quarterpallet/qp-dumpbin.png"),
                baselines=CUSTOM_FOOTPRINT,
            ),
        ),
    ),
)


def get_family(family_id: str | None) -> DisplayFamily | None:
    """Return a family by id."""
    return next((family for family in DISPLAY_FAMILIES if family.id == family_id), None)


def get_configuration(
    family: DisplayFamily, configuration_id: str | None
) -> DisplayConfiguration | None:
    """Return a configuration by id within a family."""
    return next(
        (
            configuration
            for configuration in family.configurations
            if configuration.id == configuration_id
        ),
        None,
    )


def get_baseline(
    configuration: DisplayConfiguration, baseline_id: str | None
) -> BaselineOption | None:
    """Return a baseline by id within a configuration."""
    return next(
        (baseline for baseline in configuration.baselines if baseline.id == baseline_id),
        None,
    )


def resolve_display_selection(
    family_id: str | None,
    configuration_id: str | None,
    baseline_id: str | None,
) -> DisplaySelection:
    """Resolve possibly stale ids to a valid display selection."""
    family = get_family(family_id) or DISPLAY_FAMILIES[0]
    configuration = get_configuration(family, configuration_id) or family.configurations[0]
    baseline = get_baseline(configuration, baseline_id) or configuration.baselines[0]
    return DisplaySelection(family=family, configuration=configuration, baseline=baseline)


def display_type_label(selection: DisplaySelection) -> str:
    """Return a compact compatibility label for existing v2 services."""
    return selection.family.label


def display_selection_label(selection: DisplaySelection) -> str:
    """Return the complete human-readable display selection."""
    return (
        f"{selection.family.label} - {selection.configuration.label} "
        f"{selection.baseline.label}"
    )
