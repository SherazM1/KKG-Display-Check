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


def _show_image(path: Path, caption: str, *, use_container_width: bool = True) -> None:
    """Render an image or show a visible warning when the asset is missing."""
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=use_container_width)
    else:
        st.warning(f"Missing asset: `{path}`")


def _display_template_path(display_type: str) -> Path | None:
    """Return the available base template path for a display family."""
    if display_type == "Sidekick":
        return BASE_TEMPLATE
    return None


def render_intake_panel() -> ProjectContext:
    """Render selected display and shared project fields."""
    st.markdown("### Project Details")
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
                _show_image(template_path, f"Selected display: {display_type}")

    with details_col:
        with st.container(border=True):
            field_col, image_col = st.columns([2, 1], gap="large")

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

                st.markdown("Dimensions")
                width_col, height_col, depth_col = st.columns(3, gap="medium")
                with width_col:
                    width = st.number_input("Width", min_value=1, step=1, key="v2_width")
                with height_col:
                    height = st.number_input("Height", min_value=1, step=1, key="v2_height")
                with depth_col:
                    depth = st.number_input("Depth", min_value=1, step=1, key="v2_depth")
                notes = st.text_area("Notes", key="v2_notes", height=80)

            with image_col:
                _show_image(REFERENCE_IMAGE, "Reference / Inspiration")

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
