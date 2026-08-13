"""Estimate Assistant panel for the Display Check v2 shell."""

from pathlib import Path

import streamlit as st

from app.v2.mock_data import REFERENCE_IMAGE, REFERENCE_IMAGE_NAME
from app.v2.models import EstimateResponse, PriceRange, ProjectContext
from app.v2.services.estimate_service import EstimateService


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


def render_estimate_panel(
    project: ProjectContext,
    *,
    project_ready: bool,
    reference_image_bytes: bytes | None,
    reference_image_name: str | None,
) -> None:
    """Render the mocked estimate assistant response."""
    with st.container(border=True):
        st.markdown(
            '<div class="v2-panel-heading">'
            '<div><div class="v2-card-title">Estimate Assistant</div>'
            '<div class="v2-panel-subtitle">Shared project details translated into a planning range.</div></div>'
            '<span class="v2-chip">Prototype</span></div>',
            unsafe_allow_html=True,
        )
        if not project_ready:
            st.info("Complete the required project details above to access the assistants.")

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
                '<div class="v2-placeholder-card">No reference image provided.<br>'
                "The estimate will use project details and written direction only.</div>",
                unsafe_allow_html=True,
            )

        st.text_area(
            "Estimate Prompt",
            key="v2_estimate_prompt",
            height=76,
            disabled=not project_ready,
        )
        if st.button("Estimate / Analyze", use_container_width=True, disabled=not project_ready):
            st.session_state["v2_estimate_requested"] = True

        if not project_ready:
            return

        response = EstimateService().analyze(project)

        with st.container(border=True):
            st.markdown(
                f'<div class="v2-card-title">{response.headline}</div>',
                unsafe_allow_html=True,
            )
            unit_col, program_col = st.columns(2, gap="medium")
            with unit_col:
                st.markdown('<p class="v2-result-label">Unit Range</p>', unsafe_allow_html=True)
                st.markdown(
                    '<p class="v2-estimate-value">'
                    f"{_format_price_range(response.unit_price_range, per_unit=True)}</p>",
                    unsafe_allow_html=True,
                )
            with program_col:
                st.markdown('<p class="v2-result-label">Program Range</p>', unsafe_allow_html=True)
                st.markdown(
                    '<p class="v2-estimate-value">'
                    f"{_format_price_range(response.program_price_range)}</p>",
                    unsafe_allow_html=True,
                )
            confidence_col, review_col = st.columns(2, gap="medium")
            with confidence_col:
                st.markdown('<p class="v2-result-label">Confidence</p>', unsafe_allow_html=True)
                st.markdown(
                    f'<span class="v2-badge v2-badge-green">{response.confidence}</span>',
                    unsafe_allow_html=True,
                )
            with review_col:
                st.markdown('<p class="v2-result-label">Estimator Review</p>', unsafe_allow_html=True)
                review_text = "Review recommended" if response.review_required else "Review optional"
                st.markdown(f'<span class="v2-badge">{review_text}</span>', unsafe_allow_html=True)

        basis_col, needed_col = st.columns(2, gap="medium")
        with basis_col:
            with st.container(border=True):
                st.markdown("**Estimate Basis**")
                for assumption in response.assumptions:
                    st.caption(assumption)
            with st.container(border=True):
                st.markdown("**Still Needed**")
                _render_list(response.missing_information)
        with needed_col:
            with st.container(border=True):
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
            with st.container(border=True):
                st.markdown("**What Could Change the Estimate**")
                _render_list(response.price_risks)

        if response.review_reason:
            st.caption(response.review_reason)

        st.caption(response.disclaimer)
        _render_details(response)
