"""Streamlit-independent domain contracts for Display Check v2."""

from dataclasses import dataclass, field


@dataclass
class ProjectDimensions:
    """Physical display dimensions in inches."""

    width: float | None = None
    height: float | None = None
    depth: float | None = None


@dataclass
class ProjectContext:
    """Shared project context consumed by v2 assistant services."""

    project_name: str = "Display Check Sample"
    display_type: str = "Sidekick"
    display_family: str = "sidekick"
    display_configuration: str = "hooks"
    baseline_size: str = "24"
    footprint_id: str = "sk-24-hooks"
    legacy_display_id: str = "sidekick/hooks"
    quantity: int = 500
    print_type: str = "Litho Laminate"
    shipping_packout: str = "Flat Pack"
    dimensions: ProjectDimensions = field(
        default_factory=lambda: ProjectDimensions(width=20, height=48, depth=12)
    )
    reference_image: str | None = None
    reference_image_name: str | None = None
    notes: str = ""


def is_project_ready(project: ProjectContext) -> bool:
    """Return whether required intake fields are valid."""
    return (
        bool(project.display_family.strip())
        and bool(project.display_configuration.strip())
        and bool(project.baseline_size.strip())
        and bool(project.footprint_id.strip())
        and project.quantity >= 1
        and bool(project.print_type.strip())
        and bool(project.shipping_packout.strip())
    )


@dataclass
class PriceRange:
    """Currency range for mocked estimate responses."""

    low: float
    high: float
    currency: str = "USD"


@dataclass
class EstimateDetails:
    """Technical estimate detail contract for later estimator review."""

    display_type: str
    visible_features: list[str]
    likely_hidden_features: list[str]
    material_assumptions: list[str]
    complexity: str
    technical_notes: list[str]


@dataclass
class EstimateResponse:
    """Account-team friendly mocked estimate response."""

    headline: str
    unit_price_range: PriceRange
    program_price_range: PriceRange
    assumptions: list[str]
    price_risks: list[str]
    missing_information: list[str]
    confidence: str
    review_required: bool
    review_reason: str | None
    details: EstimateDetails
    disclaimer: str


@dataclass
class VisualResponse:
    """Mock visual assistant response contract."""

    summary: str
    display_type: str
    base_template: str | None
    reference_image: str | None
    palette: list[str]
    graphic_direction: str
    placement_notes: list[str]
    warnings: list[str]
    generation_prompt: str
    confidence: str


@dataclass
class VisualConcept:
    """Future visual concept output contract."""

    image_path: str
    variation_number: int
    prompt_used: str
    selected: bool
