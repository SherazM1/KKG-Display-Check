"""Mocked estimate service for Display Check v2."""

from app.v2.models import (
    EstimateDetails,
    EstimateResponse,
    PriceRange,
    ProjectContext,
)


class EstimateService:
    """Return typed mocked estimate responses from a project context."""

    mock_unit_low = 18.0
    mock_unit_high = 24.0

    def analyze(self, project: ProjectContext) -> EstimateResponse:
        """Build a mocked estimate response using shared project fields."""
        unit_range = PriceRange(low=self.mock_unit_low, high=self.mock_unit_high)
        program_range = PriceRange(
            low=project.quantity * unit_range.low,
            high=project.quantity * unit_range.high,
        )
        dimensions_text = self._format_dimensions(project)
        display_type = project.display_type

        assumptions = [
            (
                f"For this prototype, the mock estimate assumes a standard "
                f"{display_type} configuration at {project.quantity:,} units."
            ),
            f"Print treatment is modeled as {project.print_type}.",
            f"Shipping / packout is modeled as {project.shipping_packout}.",
        ]
        if dimensions_text:
            assumptions.append(f"Working dimensions are {dimensions_text}.")

        details = EstimateDetails(
            display_type=display_type,
            visible_features=["Header", "Four shelves", "Side panels", "Base"],
            likely_hidden_features=[
                "Shelf supports",
                "Internal reinforcement",
                "Shipping carton / shipper",
            ],
            material_assumptions=[
                "Corrugated construction",
                f"{project.print_type} print treatment",
                "Standard reinforcement assumptions",
            ],
            complexity="Medium",
            technical_notes=[
                "Product weight is not yet known",
                "Final board grade is not confirmed",
                "Structural requirements require estimator validation",
            ],
        )

        return EstimateResponse(
            headline="Ballpark Estimate",
            unit_price_range=unit_range,
            program_price_range=program_range,
            assumptions=assumptions,
            price_risks=[
                "Heavier product loads requiring additional support",
                "Different board grade or material",
                "Additional dimensional features",
                "Changes to shipping or assembly method",
            ],
            missing_information=[
                "Approximate product weight",
                "Final dimensions, if not confirmed",
            ],
            confidence="Medium",
            review_required=True,
            review_reason="Recommended before sharing as a quote.",
            details=details,
            disclaimer="Ballpark estimate only - not a final quote.",
        )

    @staticmethod
    def _format_dimensions(project: ProjectContext) -> str:
        """Format dimensions when all three values are present."""
        dims = project.dimensions
        if dims.width is None or dims.height is None or dims.depth is None:
            return ""
        return f'{dims.width:g}" W x {dims.height:g}" H x {dims.depth:g}" D'
