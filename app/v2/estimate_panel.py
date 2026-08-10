"""Estimate Assistant panel for the Display Check v2 shell."""

from pathlib import Path

import streamlit as st

from app.v2.mock_data import REFERENCE_IMAGE
from app.v2.models import EstimateResponse, PriceRange, ProjectContext
from app.v2.services.estimate_service import EstimateService


def _show_image(path: Path, caption: str, *, width: int | None = None) -> None:
    """Render an image or show a visible warning when the asset is missing."""
    if path.exists():
        st.image(str(path), caption=caption, width=width)
    else:
        st.warning(f"Missing asset: `{path}`")


def _format_price_range(price_range: PriceRange, *, per_unit: bool = False) -> str:
    """Format a price range for account-team display."""
    suffix = " each" if per_unit else " total"
    return f"${price_range.low:,.0f}-${price_range.high:,.0f}{suffix}"


def _render_list(items: list[str]) -> None:
    """Render short account-team bullet lists."""
    for item in items:
        st.markdown(f"- {item}")


def _render_details(response: EstimateResponse) -> None:
    """Render technical detail fields inside an optional expander."""
    details = response.details
    with st.expander("View Estimate Details"):
        st.markdown(f"**Display Type:** {details.display_type}")
        st.markdown("**Visible Features**")
        _render_list(details.visible_features)
        st.markdown("**Likely Hidden / Support Features**")
        _render_list(details.likely_hidden_features)
        st.markdown("**Material Assumptions**")
        _render_list(details.material_assumptions)
        st.markdown(f"**Complexity:** {details.complexity}")
        st.markdown("**Technical Notes**")
        _render_list(details.technical_notes)


def render_estimate_panel(project: ProjectContext) -> None:
    """Render the mocked estimate assistant response."""
    service = EstimateService()
    response = service.analyze(project)

    with st.container(border=True):
        st.markdown('<div class="v2-card-title">Estimate Assistant</div>', unsafe_allow_html=True)
        st.caption("Uses the shared project details and reference direction for a planning range.")
        image_left, image_mid, image_right = st.columns([1, 2, 1])
        with image_mid:
            _show_image(REFERENCE_IMAGE, "Reference / Inspiration", width=220)
        st.text_area("Estimate Prompt", key="v2_estimate_prompt", height=76)
        if st.button("Estimate / Analyze", use_container_width=True):
            st.session_state["v2_estimate_requested"] = True

        st.markdown(f'<div class="v2-card-title">{response.headline}</div>', unsafe_allow_html=True)
        unit_col, program_col = st.columns(2, gap="medium")
        with unit_col:
            st.markdown('<p class="v2-result-label">Unit Range</p>', unsafe_allow_html=True)
            st.markdown(
                f'<p class="v2-result-value">{_format_price_range(response.unit_price_range, per_unit=True)}</p>',
                unsafe_allow_html=True,
            )
        with program_col:
            st.markdown('<p class="v2-result-label">Program Range</p>', unsafe_allow_html=True)
            st.markdown(
                f'<p class="v2-result-value">{_format_price_range(response.program_price_range)}</p>',
                unsafe_allow_html=True,
            )

        basis_col, needed_col = st.columns(2, gap="medium")
        with basis_col:
            st.markdown("**Estimate Basis**")
            for assumption in response.assumptions:
                st.caption(assumption)
            st.markdown("**Still Needed**")
            _render_list(response.missing_information)
        with needed_col:
            st.markdown("**What We're Accounting For**")
            _render_list(
                [
                    "Main corrugated structure",
                    "Four shelves",
                    "Shelf/support structure",
                    "Base and header",
                    "Standard internal reinforcement",
                    "Assembly and packout assumptions",
                ]
            )
            st.markdown("**What Could Change the Estimate**")
            _render_list(response.price_risks)

        confidence_col, review_col = st.columns(2, gap="medium")
        with confidence_col:
            st.markdown('<p class="v2-result-label">Confidence</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="v2-result-value">{response.confidence}</p>', unsafe_allow_html=True)
        with review_col:
            st.markdown('<p class="v2-result-label">Estimator Review</p>', unsafe_allow_html=True)
            review_text = "Recommended" if response.review_required else "Optional"
            st.markdown(f'<p class="v2-result-value">{review_text}</p>', unsafe_allow_html=True)
            if response.review_reason:
                st.caption(response.review_reason)

        st.caption(response.disclaimer)
        _render_details(response)
