"""Top toolbar for the Display Check v2 shell."""

import streamlit as st

from app.v2.state import update_project_context


def render_toolbar() -> None:
    """Render static project actions and user placeholder controls."""
    st.markdown('<div class="v2-toolbar">', unsafe_allow_html=True)
    title_col, project_col, action_col = st.columns(
        [1.2, 1.8, 2.65],
        gap="small",
        vertical_alignment="center",
    )

    with title_col:
        st.markdown(
            '<div class="v2-title-row">'
            '<div class="v2-title">Display Check 2.0</div>'
            '<span class="v2-chip">V2</span></div>',
            unsafe_allow_html=True,
        )

    with project_col:
        st.markdown('<div class="v2-field-label">Project Name</div>', unsafe_allow_html=True)
        project_name = st.text_input(
            "Project Name",
            key="v2_project_name",
            label_visibility="collapsed",
        )
        update_project_context(project_name=project_name)

    with action_col:
        new_col, save_col, export_col, viewer_col = st.columns(4, gap="small")
        with new_col:
            st.button("New Project", use_container_width=True, disabled=True)
        with save_col:
            st.button("Save Project", use_container_width=True, disabled=True)
        with export_col:
            st.button("Export", use_container_width=True, disabled=True)
        with viewer_col:
            st.markdown('<div class="v2-user-pill">Viewer</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
