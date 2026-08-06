"""Static Estimate Assistant panel for the Display Check v2 shell."""

from pathlib import Path

import streamlit as st

from app.v2.mock_data import ESTIMATE_ASSUMPTIONS, ESTIMATE_SAMPLE, REFERENCE_IMAGE


def _show_image(path: Path, caption: str) -> None:
    """Render an image or show a visible warning when the asset is missing."""
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.warning(f"Missing asset: `{path}`")


def render_estimate_panel() -> None:
    """Render the static estimate assistant UI."""
    with st.container(border=True):
        st.markdown('<div class="v2-card-title">Estimate Assistant</div>', unsafe_allow_html=True)
        st.caption("Uses the shared project details and reference direction for a planning range.")
        _show_image(REFERENCE_IMAGE, "Reference / Inspiration")
        st.text_area("Estimate Prompt", key="v2_estimate_prompt", height=110)
        st.button("Estimate / Analyze", use_container_width=True, disabled=True)

        st.markdown("#### Ballpark estimate &mdash; not a final quote.", unsafe_allow_html=True)
        result_cols = st.columns(2, gap="medium")
        for index, (label, value) in enumerate(ESTIMATE_SAMPLE.items()):
            with result_cols[index % 2]:
                st.markdown(f'<p class="v2-result-label">{label}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="v2-result-value">{value}</p>', unsafe_allow_html=True)

        st.markdown("Assumptions")
        for assumption in ESTIMATE_ASSUMPTIONS:
            st.caption(f"- {assumption}")
