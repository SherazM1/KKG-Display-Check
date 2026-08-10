"""Mocked visual service for Display Check v2."""

from app.v2.mock_data import BASE_TEMPLATE, PALETTE_SWATCHES, REFERENCE_IMAGE
from app.v2.models import ProjectContext, VisualResponse


class VisualService:
    """Return typed mocked visual responses from a project context."""

    def prepare(self, project: ProjectContext) -> VisualResponse:
        """Build a mocked visual response using shared project fields."""
        is_sidekick = project.display_type == "Sidekick"
        base_template = str(BASE_TEMPLATE) if is_sidekick else None
        reference_image = project.reference_image or str(REFERENCE_IMAGE)
        palette = [swatch["hex"] for swatch in PALETTE_SWATCHES]

        if is_sidekick:
            summary = "Mock visual direction prepared for the Sidekick base template."
            warnings = [
                "Preliminary concept only",
                "Final production artwork must be reviewed against the structural dieline",
            ]
        else:
            summary = (
                f"Mock visual direction prepared for {project.display_type}; "
                "a 3D base template is not available yet for this display family."
            )
            warnings = [
                "3D base template not available yet for this display family",
                "Preliminary concept only",
            ]

        return VisualResponse(
            summary=summary,
            display_type=project.display_type,
            base_template=base_template,
            reference_image=reference_image,
            palette=palette,
            graphic_direction=(
                "Apply the reference artwork's green, pink, and gold palette "
                f"across the {project.display_type} while preserving clear "
                "product visibility and readable branded header areas."
            ),
            placement_notes=[
                "Prioritize branding on the header",
                "Carry supporting color across shelf fronts",
                "Keep product-facing shelf areas visually clean",
                "Use side panels for secondary campaign artwork",
            ],
            warnings=warnings,
            generation_prompt=(
                f"Mock prompt for {project.display_type}: combine the blank "
                "display template, supplied reference artwork, and static palette."
            ),
            confidence="Medium",
        )
