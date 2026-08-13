"""Visual Assistant panel for the Display Check v2 shell."""

from pathlib import Path

import streamlit as st

from app.v2.mock_data import (
    PALETTE_SWATCHES,
    REFERENCE_IMAGE,
    REFERENCE_IMAGE_NAME,
    STATIC_MOCKUP,
)
from app.v2.models import ProjectContext, VisualResponse
from app.v2.services.visual_service import VisualService


def _show_image(path: Path, caption: str, *, width: int | None = None) -> None:
    """Render an image or show a visible warning when the asset is missing."""
    if path.exists():
        with st.container(border=True):
            if width is None:
                st.image(str(path), caption=caption, use_container_width=True)
            else:
                st.image(str(path), caption=caption, width=width)
    else:
        st.warning(f"Missing asset: `{path}`")


def _render_palette(response: VisualResponse) -> None:
    """Render static palette swatches from the visual response."""
    for row_start in range(0, len(PALETTE_SWATCHES), 2):
        swatch_cols = st.columns(2, gap="small")
        row_swatches = PALETTE_SWATCHES[row_start : row_start + 2]
        row_colors = response.palette[row_start : row_start + 2]
        for swatch_col, swatch, color in zip(swatch_cols, row_swatches, row_colors):
            with swatch_col:
                st.markdown(
                    f'<div class="v2-swatch" style="background:{color};"></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="v2-swatch-label">{swatch["label"]}</div>',
                    unsafe_allow_html=True,
                )


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
        st.markdown(
            '<div class="v2-panel-heading">'
            '<div><div class="v2-card-title">Visual Assistant</div>'
            '<div class="v2-panel-subtitle">Template, reference, palette, and concept direction.</div></div>'
            '<span class="v2-chip">Mocked</span></div>',
            unsafe_allow_html=True,
        )
        if not project_ready:
            st.info("Complete the required project details above to access the assistants.")

        base_col, reference_col = st.columns(2, gap="medium")
        with base_col:
            st.markdown('<div class="v2-section-kicker">Base template</div>', unsafe_allow_html=True)
            if response.base_template is None:
                st.info("3D base template not available yet for this display family.")
            else:
                _show_image(Path(response.base_template), "Blank Sidekick template", width=170)
        with reference_col:
            st.markdown('<div class="v2-section-kicker">Reference / inspiration</div>', unsafe_allow_html=True)
            if reference_image_bytes:
                with st.container(border=True):
                    st.image(
                        reference_image_bytes,
                        caption=f"Reference / Inspiration: {reference_image_name}",
                        use_container_width=True,
                    )
            elif REFERENCE_IMAGE.exists():
                _show_image(REFERENCE_IMAGE, f"Demo reference: {REFERENCE_IMAGE_NAME}")
            else:
                st.markdown(
                    '<div class="v2-placeholder-card">Add a reference image for stronger visual direction.</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<div class="v2-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="v2-card-title">Color Direction</div>',
            unsafe_allow_html=True,
        )
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

        st.markdown('<div class="v2-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="v2-panel-heading">'
            '<div><div class="v2-card-title">Preliminary Mockup</div>'
            '<div class="v2-panel-subtitle">Static concept for early account-team review.</div></div>'
            '<span class="v2-badge v2-badge-green">Concept</span></div>',
            unsafe_allow_html=True,
        )
        caption = (
            "Preliminary mockup - not final art"
            if reference_image_bytes
            else "Sample mock preliminary concept"
        )
        _show_image(STATIC_MOCKUP, caption)
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
