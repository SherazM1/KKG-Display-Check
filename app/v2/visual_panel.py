"""Static Visual Assistant panel for the Display Check v2 shell."""

from pathlib import Path

import streamlit as st

from app.v2.mock_data import BASE_TEMPLATE, PALETTE_SWATCHES, REFERENCE_IMAGE, STATIC_MOCKUP


def _show_image(path: Path, caption: str) -> None:
    """Render an image or show a visible warning when the asset is missing."""
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.warning(f"Missing asset: `{path}`")


def render_visual_panel() -> None:
    """Render the static visual assistant UI."""
    with st.container(border=True):
        st.markdown('<div class="v2-card-title">Visual Assistant</div>', unsafe_allow_html=True)

        base_col, reference_col = st.columns(2, gap="medium")
        with base_col:
            _show_image(BASE_TEMPLATE, "Base Template")
        with reference_col:
            _show_image(REFERENCE_IMAGE, "Reference / Inspiration")

        st.markdown("#### Color Direction")
        swatch_cols = st.columns(4, gap="small")
        for swatch_col, swatch in zip(swatch_cols, PALETTE_SWATCHES):
            with swatch_col:
                st.markdown(
                    f'<div class="v2-swatch" style="background:{swatch["hex"]};"></div>',
                    unsafe_allow_html=True,
                )
                st.caption(swatch["label"])

        st.text_area("Visual Direction", key="v2_visual_direction", height=110)
        st.button("Create Visual", use_container_width=True, disabled=True)

        st.markdown("#### Preliminary Mockup")
        _show_image(STATIC_MOCKUP, "Preliminary mockup &mdash; not final art")

        action_col, save_col = st.columns(2, gap="small")
        with action_col:
            st.button("Regenerate", use_container_width=True, disabled=True)
        with save_col:
            st.button("Save Concept", use_container_width=True, disabled=True)
