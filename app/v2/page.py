"""Page assembly for the Display Check v2 Streamlit shell."""

import streamlit as st

from app.v2.estimate_panel import render_estimate_panel
from app.v2.intake_panel import render_intake_panel
from app.v2.navigation import render_navigation
from app.v2.state import get_project_context, initialize_v2_state
from app.v2.toolbar import render_toolbar
from app.v2.visual_panel import render_visual_panel


def _inject_styles() -> None:
    """Apply light, isolated styling for the v2 Streamlit shell."""
    st.markdown(
        """
        <style>
          :root {
            --v2-border: #e5e7eb;
            --v2-muted: #667085;
            --v2-ink: #101828;
          }
          .v2-toolbar {
            border-bottom: 1px solid var(--v2-border);
            padding: 0 0 0.35rem;
            margin-bottom: 0.45rem;
          }
          .v2-title {
            color: var(--v2-ink);
            font-size: 1.35rem;
            font-weight: 700;
            line-height: 1.2;
          }
          .v2-muted {
            color: var(--v2-muted);
            font-size: 0.82rem;
          }
          .v2-card-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0;
          }
          .v2-result-label {
            color: var(--v2-muted);
            font-size: 0.78rem;
            margin-bottom: 0;
          }
          .v2-result-value {
            color: var(--v2-ink);
            font-size: 0.98rem;
            font-weight: 650;
            margin: 0 0 0.25rem;
          }
          .v2-swatch {
            border: 1px solid var(--v2-border);
            border-radius: 6px;
            height: 30px;
            width: 100%;
          }
          .v2-user-pill {
            border: 1px solid var(--v2-border);
            border-radius: 999px;
            color: var(--v2-muted);
            padding: 0.35rem 0.65rem;
            text-align: center;
            white-space: nowrap;
          }
          .v2-compact-section {
            margin: 0.35rem 0 0.2rem;
          }
          .v2-tight-copy p,
          .v2-tight-copy ul {
            margin-bottom: 0.25rem;
          }
          div[data-testid="stVerticalBlock"] {
            gap: 0.45rem;
          }
          div[data-testid="stMarkdownContainer"] p {
            margin-bottom: 0.25rem;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page() -> None:
    """Render the complete visual-only Display Check v2 experience."""
    initialize_v2_state()
    _inject_styles()
    render_toolbar()
    render_intake_panel()
    project = get_project_context()

    left_col, right_col = st.columns(2, gap="large")
    with left_col:
        render_estimate_panel(project)
    with right_col:
        render_visual_panel(project)

    render_navigation()
