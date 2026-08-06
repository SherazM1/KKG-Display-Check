"""Bottom navigation summary for the Display Check v2 shell."""

import streamlit as st


def render_navigation() -> None:
    """Render static bottom tabs for the v2 shell."""
    st.markdown("### Workspace Summary")
    estimate_tab, visual_tab, summary_tab = st.tabs(["Estimate", "Visual", "Project Summary"])

    with estimate_tab:
        st.caption("Static planning range is visible in the Estimate Assistant panel.")
    with visual_tab:
        st.caption("Static base, reference, color direction, and preliminary mockup are visible.")
    with summary_tab:
        st.caption("Project summary placeholders will collect selected display, intake fields, and assistant outputs.")
