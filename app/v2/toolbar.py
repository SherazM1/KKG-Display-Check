"""Top toolbar for the Display Check v2 shell."""

import streamlit as st


def render_toolbar() -> None:
    """Render static project actions and user placeholder controls."""
    st.markdown('<div class="v2-toolbar">', unsafe_allow_html=True)
    title_col, project_col, action_col, user_col = st.columns(
        [1.45, 1.55, 1.9, 0.8],
        gap="medium",
        vertical_alignment="center",
    )

    with title_col:
        st.markdown('<div class="v2-title">Display Check 2.0</div>', unsafe_allow_html=True)
        st.markdown('<div class="v2-muted">Visual planning workspace</div>', unsafe_allow_html=True)

    with project_col:
        st.text_input("Project Name", key="v2_project_name")

    with action_col:
        new_col, save_col, export_col = st.columns(3, gap="small")
        with new_col:
            st.button("New Project", use_container_width=True, disabled=True)
        with save_col:
            st.button("Save Project", use_container_width=True, disabled=True)
        with export_col:
            st.button("Export", use_container_width=True, disabled=True)

    with user_col:
        st.markdown('<div class="v2-user-pill">Viewer</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
