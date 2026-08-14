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
from app.v2.state import (
    clear_reference_image,
    get_reference_image_bytes,
    get_reference_image_name,
    get_reference_uploader_key,
    set_reference_image,
    update_project_context,
)
from app.v2.uploads import UploadValidationError, sanitize_image_upload


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


def _render_reference_uploader() -> None:
    """Render the session-only reference image uploader and preview."""
    uploaded = st.file_uploader(
        "Reference / Inspiration",
        type=["png", "jpg", "jpeg", "webp"],
        key=get_reference_uploader_key(),
    )
    st.caption("10 MB max - PNG, JPG, JPEG, WEBP")
    if uploaded is not None:
        try:
            sanitized = sanitize_image_upload(
                image_bytes=uploaded.getvalue(),
                filename=uploaded.name,
                mime_type=uploaded.type,
            )
        except UploadValidationError as exc:
            st.error(str(exc))
        else:
            set_reference_image(
                image_bytes=sanitized.image_bytes,
                name=uploaded.name,
                mime=sanitized.mime_type,
            )

    image_bytes = get_reference_image_bytes()
    image_name = get_reference_image_name()
    if image_bytes is None:
        if REFERENCE_IMAGE.exists():
            with st.container(border=True):
                st.image(
                    str(REFERENCE_IMAGE),
                    caption="Demo reference",
                    use_container_width=True,
                )
        else:
            st.markdown(
                '<div class="v2-placeholder-card">Optional reference image<br>'
                "PNG, JPG, JPEG, or WEBP up to 10 MB.</div>",
                unsafe_allow_html=True,
            )
        return

    with st.container(border=True):
        st.image(
            image_bytes,
            caption=image_name or "Reference image",
            use_container_width=True,
        )
    if st.button("Remove Reference", use_container_width=True):
        clear_reference_image()
        st.rerun()


def _display_template_path(display_type: str) -> Path | None:
    """Return the available base template path for a display family."""
    if display_type == "Sidekick":
        return BASE_TEMPLATE
    return None


def _option_label(option: str) -> str:
    """Render a quiet placeholder for required select boxes."""
    return option or "Select..."


def render_intake_panel() -> ProjectContext:
    """Render selected display and shared project fields."""
    display_col, details_col = st.columns([0.85, 3.15], gap="large")

    with display_col:
        with st.container(border=True):
            st.markdown(
                '<div class="v2-card-title">Display Type</div>',
                unsafe_allow_html=True,
            )
            display_type = st.selectbox(
                "Display Type",
                ["", *DISPLAY_OPTIONS],
                key="v2_display_type",
                label_visibility="collapsed",
                format_func=_option_label,
            )
            template_path = _display_template_path(display_type)
            if template_path is None:
                st.info("3D base template not available yet for this display family.")
            else:
                _show_image(template_path, f"Selected display: {display_type}", width=170)

    with details_col:
        with st.container(border=True):
            field_col, image_col = st.columns([2.45, 1], gap="medium")

            with field_col:
                st.markdown('<div class="v2-panel-subtitle">Core specs</div>', unsafe_allow_html=True)
                qty_col, print_col, ship_col = st.columns(3, gap="medium")
                with qty_col:
                    quantity = st.number_input("Quantity", min_value=1, step=25, key="v2_quantity")
                with print_col:
                    print_type = st.selectbox(
                        "Print Type",
                        ["", *PRINT_TYPE_OPTIONS],
                        key="v2_print_type",
                        format_func=_option_label,
                    )
                with ship_col:
                    shipping_packout = st.selectbox(
                        "Shipping / Packout",
                        ["", *SHIPPING_PACKOUT_OPTIONS],
                        key="v2_shipping_packout",
                        format_func=_option_label,
                    )

                width_col, height_col, depth_col = st.columns(3, gap="medium")
                with width_col:
                    width = st.number_input("Width", min_value=1, step=1, key="v2_width")
                with height_col:
                    height = st.number_input("Height", min_value=1, step=1, key="v2_height")
                with depth_col:
                    depth = st.number_input("Depth", min_value=1, step=1, key="v2_depth")
                notes = st.text_area("Notes", key="v2_notes", height=52)

            with image_col:
                st.markdown(
                    '<div class="v2-panel-subtitle">Shared reference</div>',
                    unsafe_allow_html=True,
                )
                _render_reference_uploader()

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
        reference_image="session" if get_reference_image_bytes() else None,
        reference_image_name=get_reference_image_name(),
        notes=notes,
    )
