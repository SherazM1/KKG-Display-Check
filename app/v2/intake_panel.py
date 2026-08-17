"""Project intake area for the Display Check v2 shell."""

from pathlib import Path

import streamlit as st

from app.v2.display_registry import (
    DISPLAY_FAMILIES,
    DisplayConfiguration,
    DisplayFamily,
    DisplaySelection,
    display_type_label,
    resolve_display_selection,
)
from app.v2.mock_data import (
    BASE_TEMPLATE,
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


def _display_template_path(selection: DisplaySelection) -> Path | None:
    """Return the available base template path for a display family."""
    if selection.family.id == "sidekick":
        return BASE_TEMPLATE
    return None


def _option_label(option: str) -> str:
    """Render a quiet placeholder for required select boxes."""
    return option or "Select..."


def _family_label(family_id: str) -> str:
    """Return the display label for a family id."""
    selection = resolve_display_selection(family_id, None, None)
    return selection.family.label


def _configuration_label(family: DisplayFamily, configuration_id: str) -> str:
    """Return the display label for a configuration id."""
    selection = resolve_display_selection(family.id, configuration_id, None)
    return selection.configuration.label


def _baseline_label(configuration: DisplayConfiguration, baseline_id: str) -> str:
    """Return the display label for a baseline id."""
    selection = resolve_display_selection(None, None, None)
    baseline = next(
        (
            option
            for option in configuration.baselines
            if option.id == baseline_id
        ),
        selection.baseline,
    )
    return baseline.label


def _sync_display_selection() -> DisplaySelection:
    """Normalize stale Streamlit display selection keys to valid registry ids."""
    selection = resolve_display_selection(
        st.session_state.get("v2_display_family"),
        st.session_state.get("v2_display_configuration"),
        st.session_state.get("v2_baseline_size"),
    )
    st.session_state["v2_display_family"] = selection.family.id
    st.session_state["v2_display_configuration"] = selection.configuration.id
    st.session_state["v2_baseline_size"] = selection.baseline.id
    return selection


def render_intake_panel() -> ProjectContext:
    """Render selected display and shared project fields."""
    display_col, details_col = st.columns([0.85, 3.15], gap="large")

    with display_col:
        with st.container(border=True):
            selection = _sync_display_selection()
            family_id = st.selectbox(
                "Display Family",
                [family.id for family in DISPLAY_FAMILIES],
                key="v2_display_family",
                format_func=_family_label,
            )
            selection = resolve_display_selection(
                family_id,
                st.session_state.get("v2_display_configuration"),
                st.session_state.get("v2_baseline_size"),
            )
            st.session_state["v2_display_configuration"] = selection.configuration.id
            st.session_state["v2_baseline_size"] = selection.baseline.id

            configuration_id = st.selectbox(
                "Configuration",
                [configuration.id for configuration in selection.family.configurations],
                key="v2_display_configuration",
                format_func=lambda value: _configuration_label(selection.family, value),
            )
            selection = resolve_display_selection(
                family_id,
                configuration_id,
                st.session_state.get("v2_baseline_size"),
            )
            st.session_state["v2_baseline_size"] = selection.baseline.id

            baseline_id = st.selectbox(
                "Baseline Size / Footprint",
                [baseline.id for baseline in selection.configuration.baselines],
                key="v2_baseline_size",
                format_func=lambda value: _baseline_label(selection.configuration, value),
            )
            selection = resolve_display_selection(family_id, configuration_id, baseline_id)

            template_path = _display_template_path(selection)
            if template_path is None:
                st.info("3D base template not available yet for this display family.")
            else:
                _show_image(template_path, selection.family.label, width=150)
            st.session_state["v2_display_type"] = display_type_label(selection)

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
        display_type=display_type_label(selection),
        display_family=selection.family.id,
        display_configuration=selection.configuration.id,
        baseline_size=selection.baseline.id,
        footprint_id=selection.baseline.footprint_id,
        legacy_display_id=selection.configuration.legacy_id,
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
