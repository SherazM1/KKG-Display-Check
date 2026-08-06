"""Project intake area for the Display Check v2 shell."""

from pathlib import Path

import streamlit as st

from app.v2.mock_data import BASE_TEMPLATE, REFERENCE_IMAGE


def _show_image(path: Path, caption: str, *, use_container_width: bool = True) -> None:
    """Render an image or show a visible warning when the asset is missing."""
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=use_container_width)
    else:
        st.warning(f"Missing asset: `{path}`")


def render_intake_panel() -> None:
    """Render selected display and shared project fields."""
    st.markdown("### Project Details")
    display_col, details_col = st.columns([1, 3], gap="large")

    with display_col:
        with st.container(border=True):
            st.markdown('<div class="v2-card-title">Select Display Type</div>', unsafe_allow_html=True)
            st.selectbox(
                "Display Type",
                ["Sidekick"],
                key="v2_display_type",
                label_visibility="collapsed",
            )
            _show_image(BASE_TEMPLATE, "Selected display: Sidekick")

    with details_col:
        with st.container(border=True):
            field_col, image_col = st.columns([2, 1], gap="large")

            with field_col:
                qty_col, print_col, ship_col = st.columns(3, gap="medium")
                with qty_col:
                    st.number_input("Quantity", min_value=1, step=25, key="v2_quantity")
                with print_col:
                    st.selectbox(
                        "Print Type",
                        ["Litho Laminate", "Digital Print", "Flexo Print"],
                        key="v2_print_type",
                    )
                with ship_col:
                    st.selectbox(
                        "Shipping / Packout",
                        ["Flat Pack", "Assembled", "Retail Ready"],
                        key="v2_shipping_packout",
                    )

                st.markdown("Dimensions")
                width_col, height_col, depth_col = st.columns(3, gap="medium")
                with width_col:
                    st.number_input("Width", min_value=1, step=1, key="v2_width")
                with height_col:
                    st.number_input("Height", min_value=1, step=1, key="v2_height")
                with depth_col:
                    st.number_input("Depth", min_value=1, step=1, key="v2_depth")

            with image_col:
                _show_image(REFERENCE_IMAGE, "Reference / Inspiration")
