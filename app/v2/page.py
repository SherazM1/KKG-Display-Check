"""Page assembly for the Display Check v2 Streamlit shell."""

import streamlit as st

from app.v2.estimate_panel import render_estimate_panel
from app.v2.intake_panel import render_intake_panel
from app.v2.navigation import render_navigation
from app.v2.models import is_project_ready
from app.v2.state import (
    get_project_context,
    get_reference_image_bytes,
    get_reference_image_name,
    initialize_v2_state,
)
from app.v2.toolbar import render_toolbar
from app.v2.visual_panel import render_visual_panel


def _inject_styles() -> None:
    """Apply light, isolated styling for the v2 Streamlit shell."""
    st.markdown(
        """
        <style>
          :root {
            --v2-accent: #22675d;
            --v2-accent-soft: #e8f2ef;
            --v2-border: #d8dee6;
            --v2-card: #ffffff;
            --v2-muted: #5f6b7a;
            --v2-ink: #101828;
            --v2-soft: #f5f7f9;
          }
          .block-container,
          .block-container * {
            box-sizing: border-box;
          }
          .block-container {
            max-width: 1380px;
            padding-top: 1.15rem;
            padding-bottom: 2.2rem;
          }
          .v2-toolbar {
            background: linear-gradient(180deg, #ffffff 0%, #f7faf9 100%);
            border: 1px solid var(--v2-border);
            border-radius: 12px;
            box-shadow: 0 12px 30px rgba(16, 24, 40, 0.06);
            padding: 0.7rem 0.85rem 0.35rem;
            margin-bottom: 0.75rem;
          }
          .v2-title {
            color: var(--v2-ink);
            font-size: 1.48rem;
            font-weight: 760;
            line-height: 1.2;
          }
          .v2-title-row {
            align-items: center;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            min-width: 0;
          }
          .v2-chip {
            background: var(--v2-accent-soft);
            border: 1px solid #c8ded8;
            border-radius: 999px;
            color: #24584f;
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 700;
            line-height: 1;
            max-width: 100%;
            padding: 0.28rem 0.48rem;
            text-transform: uppercase;
            white-space: normal;
          }
          .v2-muted {
            color: var(--v2-muted);
            font-size: 0.82rem;
          }
          .v2-section-kicker {
            color: var(--v2-accent);
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0;
            margin-bottom: 0.05rem;
            text-transform: uppercase;
          }
          .v2-card-title {
            font-size: 1.05rem;
            font-weight: 760;
            margin-bottom: 0.18rem;
            min-width: 0;
            overflow-wrap: anywhere;
          }
          .v2-panel-heading {
            align-items: center;
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            justify-content: space-between;
            margin-bottom: 0.25rem;
            min-width: 0;
          }
          .v2-panel-subtitle {
            color: var(--v2-muted);
            font-size: 0.8rem;
            margin: -0.12rem 0 0.28rem;
            min-width: 0;
            overflow-wrap: anywhere;
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
          .v2-estimate-hero {
            background: linear-gradient(135deg, #f7faf9 0%, #ffffff 100%);
            border: 1px solid var(--v2-border);
            border-radius: 10px;
            box-shadow: inset 3px 0 0 var(--v2-accent);
            padding: 0.7rem 0.85rem;
            margin: 0.35rem 0 0.55rem;
          }
          .v2-estimate-value {
            color: var(--v2-ink);
            font-size: 1.18rem;
            font-weight: 780;
            margin: 0;
            overflow-wrap: anywhere;
          }
          .v2-badge {
            background: #f8f4e8;
            border: 1px solid #ead9a7;
            border-radius: 999px;
            color: #7a5b12;
            display: inline-block;
            font-size: 0.76rem;
            font-weight: 700;
            line-height: 1.15;
            margin: 0 0.25rem 0.25rem 0;
            max-width: 100%;
            overflow-wrap: anywhere;
            padding: 0.22rem 0.52rem;
            white-space: normal;
          }
          .v2-badge-green {
            background: var(--v2-accent-soft);
            border-color: #c8ded8;
            color: #24584f;
          }
          .v2-image-card {
            background: radial-gradient(circle at top, #ffffff 0%, #f3f6f8 100%);
            border: 1px solid var(--v2-border);
            border-radius: 10px;
            padding: 0.65rem;
            text-align: center;
          }
          .v2-placeholder-card {
            background: var(--v2-soft);
            border: 1px dashed #cbd5df;
            border-radius: 10px;
            color: var(--v2-muted);
            font-size: 0.8rem;
            min-height: 120px;
            padding: 1rem 0.75rem;
            text-align: center;
            overflow-wrap: anywhere;
          }
          .v2-swatch {
            border: 1px solid var(--v2-border);
            border-radius: 8px;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
            height: 32px;
            max-width: 100%;
            width: 100%;
          }
          .v2-swatch-label {
            color: var(--v2-muted);
            font-size: 0.7rem;
            line-height: 1.15;
            margin: 0.18rem auto 0.15rem;
            max-width: 100%;
            min-height: 1.65rem;
            overflow-wrap: anywhere;
            text-align: center;
            white-space: normal;
          }
          .v2-user-pill {
            background: #ffffff;
            border: 1px solid var(--v2-border);
            border-radius: 999px;
            color: var(--v2-muted);
            display: inline-block;
            max-width: 100%;
            overflow-wrap: anywhere;
            padding: 0.35rem 0.65rem;
            text-align: center;
            white-space: normal;
          }
          .v2-compact-section {
            margin: 0.35rem 0 0.2rem;
          }
          .v2-tight-copy p,
          .v2-tight-copy ul {
            margin-bottom: 0.25rem;
          }
          .v2-list-card {
            background: #fbfcfd;
            border: 1px solid #e4e9ef;
            border-radius: 10px;
            padding: 0.55rem 0.72rem;
          }
          .v2-divider {
            border-top: 1px solid var(--v2-border);
            margin: 0.45rem 0;
          }
          div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--v2-card);
            border-color: var(--v2-border);
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(16, 24, 40, 0.045);
            min-width: 0;
            overflow: hidden;
          }
          div[data-testid="column"] {
            min-width: 0;
          }
          div[data-testid="stImage"] {
            max-width: 100%;
            min-width: 0;
            text-align: center;
          }
          div[data-testid="stImage"] img {
            display: block;
            height: auto;
            margin-left: auto;
            margin-right: auto;
            max-height: 360px;
            max-width: 100%;
            object-fit: contain;
          }
          div[data-testid="stImageCaption"] {
            max-width: 100%;
            overflow-wrap: anywhere;
            text-align: center;
          }
          div[data-testid="stButton"] > button {
            border-radius: 8px;
            font-weight: 650;
            min-width: 0;
            overflow-wrap: anywhere;
            white-space: normal;
          }
          div[data-testid="stTabs"] button {
            font-weight: 650;
          }
          div[data-testid="stVerticalBlock"] {
            gap: 0.45rem;
          }
          div[data-testid="stMarkdownContainer"] p {
            margin-bottom: 0.25rem;
            min-width: 0;
            overflow-wrap: anywhere;
          }
          div[data-testid="stMarkdownContainer"] li {
            overflow-wrap: anywhere;
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
    project_ready = is_project_ready(project)
    reference_image_bytes = get_reference_image_bytes()
    reference_image_name = get_reference_image_name()

    left_col, right_col = st.columns(2, gap="large")
    with left_col:
        render_estimate_panel(
            project,
            project_ready=project_ready,
            reference_image_bytes=reference_image_bytes,
            reference_image_name=reference_image_name,
        )
    with right_col:
        render_visual_panel(
            project,
            project_ready=project_ready,
            reference_image_bytes=reference_image_bytes,
            reference_image_name=reference_image_name,
        )

    render_navigation()
