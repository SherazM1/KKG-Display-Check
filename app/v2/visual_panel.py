"""Visual Assistant panel for the Display Check v2 shell."""

from pathlib import Path

import streamlit as st

from app.v2.mock_data import PALETTE_SWATCHES, REFERENCE_IMAGE, STATIC_MOCKUP
from app.v2.models import ProjectContext, VisualResponse
from app.v2.services.visual_service import VisualService


def _show_image(path: Path, caption: str, *, width: int | None = None) -> None:
    """Render an image or show a visible warning when the asset is missing."""
    if path.exists():
        st.image(str(path), caption=caption, width=width)
    else:
        st.warning(f"Missing asset: `{path}`")


def _render_palette(response: VisualResponse) -> None:
    """Render static palette swatches from the visual response."""
    swatch_cols = st.columns(4, gap="small")
    for swatch_col, swatch, color in zip(swatch_cols, PALETTE_SWATCHES, response.palette):
        with swatch_col:
            st.markdown(
                f'<div class="v2-swatch" style="background:{color};"></div>',
                unsafe_allow_html=True,
            )
            st.caption(swatch["label"])


def render_visual_panel(
    project: ProjectContext,
    *,
    project_ready: bool,
    reference_image_bytes: bytes | None,
    reference_image_name: str | None,
) -> None:
    """Render the mocked visual assistant response."""
    service = VisualService()
    response = service.prepare(project)

    with st.container(border=True):
        st.markdown('<div class="v2-card-title">Visual Assistant</div>', unsafe_allow_html=True)
        if not project_ready:
            st.info("Complete the required project details above to access the assistants.")

        base_col, reference_col = st.columns(2, gap="medium")
        with base_col:
            if response.base_template is None:
                st.info("3D base template not available yet for this display family.")
            else:
                base_left, base_mid, base_right = st.columns([1, 3, 1])
                with base_mid:
                    _show_image(Path(response.base_template), "Base Template", width=170)
        with reference_col:
            if reference_image_bytes:
                st.image(
                    reference_image_bytes,
                    caption=f"Reference / Inspiration: {reference_image_name}",
                    width=230,
                )
            else:
                st.caption("Add a reference image for stronger visual direction.")

        st.markdown('<div class="v2-card-title">Color Direction</div>', unsafe_allow_html=True)
        st.caption(response.graphic_direction)
        _render_palette(response)

        st.text_area(
            "Visual Direction",
            key="v2_visual_direction",
            height=76,
            disabled=not project_ready,
        )
        if st.button("Create Visual", use_container_width=True, disabled=not project_ready):
            st.session_state["v2_visual_requested"] = True

        st.markdown('<div class="v2-card-title">Preliminary Mockup</div>', unsafe_allow_html=True)
        mock_left, mock_mid, mock_right = st.columns([1, 4, 1])
        with mock_mid:
            caption = (
                "Preliminary mockup &mdash; not final art"
                if reference_image_bytes
                else "Sample mock preliminary concept"
            )
            _show_image(STATIC_MOCKUP, caption, width=380)
        st.caption(response.summary)

        with st.expander("View Visual Notes"):
            st.markdown("**Placement Notes**")
            for note in response.placement_notes:
                st.markdown(f"- {note}")
            st.markdown("**Warnings**")
            for warning in response.warnings:
                st.markdown(f"- {warning}")
            st.markdown(f"**Confidence:** {response.confidence}")

        action_col, save_col = st.columns(2, gap="small")
        with action_col:
            st.button("Regenerate", use_container_width=True, disabled=True)
        with save_col:
            st.button("Save Concept", use_container_width=True, disabled=True)
