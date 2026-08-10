"""Project intake area for the Display Check v2 shell."""

from pathlib import Path

import streamlit as st

from app.v2.mock_data import (
    BASE_TEMPLATE,
    DISPLAY_OPTIONS,
    PRINT_TYPE_OPTIONS,
    REFERENCE_IMAGE,
    SHIPPING_PACKOUT_OPTIONS,
)
from app.v2.models import ProjectContext, ProjectDimensions
from app.v2.state import update_project_context


def _show_image(path: Path, caption: str, *, width: int | None = None) -> None:
    """Render an image or show a visible warning when the asset is missing."""
    if path.exists():
        st.image(str(path), caption=caption, width=width)
    else:
        st.warning(f"Missing asset: `{path}`")


def _display_template_path(display_type: str) -> Path | None:
    """Return the available base template path for a display family."""
    if display_type == "Sidekick":
        return BASE_TEMPLATE
    return None


def render_intake_panel() -> ProjectContext:
    """Render selected display and shared project fields."""
    st.markdown('<div class="v2-card-title">Project Details</div>', unsafe_allow_html=True)
    display_col, details_col = st.columns([1, 3], gap="large")

    with display_col:
        with st.container(border=True):
            st.markdown('<div class="v2-card-title">Select Display Type</div>', unsafe_allow_html=True)
            display_type = st.selectbox(
                "Display Type",
                DISPLAY_OPTIONS,
                key="v2_display_type",
                label_visibility="collapsed",
            )
            template_path = _display_template_path(display_type)
            if template_path is None:
                st.info("3D base template not available yet for this display family.")
            else:
                preview_left, preview_mid, preview_right = st.columns([1, 4, 1])
                with preview_mid:
                    _show_image(template_path, f"Selected display: {display_type}", width=170)

    with details_col:
        with st.container(border=True):
            field_col, image_col = st.columns([2.45, 1], gap="medium")

            with field_col:
                qty_col, print_col, ship_col = st.columns(3, gap="medium")
                with qty_col:
                    quantity = st.number_input("Quantity", min_value=1, step=25, key="v2_quantity")
                with print_col:
                    print_type = st.selectbox(
                        "Print Type",
                        PRINT_TYPE_OPTIONS,
                        key="v2_print_type",
                    )
                with ship_col:
                    shipping_packout = st.selectbox(
                        "Shipping / Packout",
                        SHIPPING_PACKOUT_OPTIONS,
                        key="v2_shipping_packout",
                    )

                width_col, height_col, depth_col, notes_col = st.columns(
                    [1, 1, 1, 2.2],
                    gap="medium",
                )
                with width_col:
                    width = st.number_input("Width", min_value=1, step=1, key="v2_width")
                with height_col:
                    height = st.number_input("Height", min_value=1, step=1, key="v2_height")
                with depth_col:
                    depth = st.number_input("Depth", min_value=1, step=1, key="v2_depth")
                with notes_col:
                    notes = st.text_area("Notes", key="v2_notes", height=52)

            with image_col:
                _show_image(REFERENCE_IMAGE, "Reference / Inspiration", width=220)

    return update_project_context(
        display_type=display_type,
        quantity=int(quantity),
        print_type=print_type,
        shipping_packout=shipping_packout,
        dimensions=ProjectDimensions(
            width=float(width),
            height=float(height),
            depth=float(depth),
        ),
        reference_image=str(REFERENCE_IMAGE),
        notes=notes,
    )
