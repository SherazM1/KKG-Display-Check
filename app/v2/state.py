"""Session-state initialization for the Display Check v2 shell."""

import streamlit as st

from app.v2.mock_data import PROJECT_DEFAULTS


def init_state() -> None:
    """Initialize only the namespaced defaults needed for the v2 UI."""
    for key, value in PROJECT_DEFAULTS.items():
        st.session_state.setdefault(f"v2_{key}", value)

    st.session_state.setdefault(
        "v2_estimate_prompt",
        "Review the reference direction against the selected Sidekick display.",
    )
    st.session_state.setdefault(
        "v2_visual_direction",
        "Apply the reference palette to the blank Sidekick structure with a clean retail presentation.",
    )
