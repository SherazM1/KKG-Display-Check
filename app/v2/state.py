"""Shared Streamlit state helpers for the Display Check v2 shell."""

from dataclasses import replace

import streamlit as st

from app.v2.models import ProjectContext, ProjectDimensions


PROJECT_CONTEXT_KEY = "v2_project_context"
REFERENCE_IMAGE_BYTES_KEY = "v2_reference_image_bytes"
REFERENCE_IMAGE_NAME_KEY = "v2_reference_image_name"
REFERENCE_IMAGE_MIME_KEY = "v2_reference_image_mime"
REFERENCE_UPLOADER_VERSION_KEY = "v2_reference_uploader_version"


def _default_project_context() -> ProjectContext:
    """Create the default shared project context."""
    return ProjectContext(
        dimensions=ProjectDimensions(width=20, height=48, depth=12),
    )


def initialize_v2_state() -> None:
    """Initialize namespaced v2 session keys and widget defaults."""
    context = st.session_state.setdefault(PROJECT_CONTEXT_KEY, _default_project_context())
    st.session_state.setdefault("v2_project_name", context.project_name)
    st.session_state.setdefault("v2_display_type", context.display_type)
    st.session_state.setdefault("v2_display_family", context.display_family)
    st.session_state.setdefault("v2_display_configuration", context.display_configuration)
    st.session_state.setdefault("v2_baseline_size", context.baseline_size)
    st.session_state.setdefault("v2_quantity", context.quantity)
    st.session_state.setdefault("v2_print_type", context.print_type)
    st.session_state.setdefault("v2_shipping_packout", context.shipping_packout)
    st.session_state.setdefault("v2_width", context.dimensions.width)
    st.session_state.setdefault("v2_height", context.dimensions.height)
    st.session_state.setdefault("v2_depth", context.dimensions.depth)
    st.session_state.setdefault("v2_notes", context.notes)
    st.session_state.setdefault(REFERENCE_IMAGE_BYTES_KEY, None)
    st.session_state.setdefault(REFERENCE_IMAGE_NAME_KEY, context.reference_image_name)
    st.session_state.setdefault(REFERENCE_IMAGE_MIME_KEY, None)
    st.session_state.setdefault(REFERENCE_UPLOADER_VERSION_KEY, 0)
    st.session_state.setdefault(
        "v2_estimate_prompt",
        "Review the reference direction against the selected display.",
    )
    st.session_state.setdefault(
        "v2_visual_direction",
        "Apply the reference palette to the selected display with a clean retail presentation.",
    )


def get_project_context() -> ProjectContext:
    """Return the single authoritative v2 project context."""
    return st.session_state[PROJECT_CONTEXT_KEY]


def update_project_context(**changes: object) -> ProjectContext:
    """Update the shared project context without embedding business logic."""
    context = get_project_context()
    dimensions = changes.pop("dimensions", None)

    if dimensions is not None and not isinstance(dimensions, ProjectDimensions):
        raise TypeError("dimensions must be a ProjectDimensions instance")

    updated = replace(context, **changes)
    if dimensions is not None:
        updated = replace(updated, dimensions=dimensions)

    st.session_state[PROJECT_CONTEXT_KEY] = updated
    return updated


def get_reference_image_bytes() -> bytes | None:
    """Return the session-only uploaded reference bytes."""
    return st.session_state.get(REFERENCE_IMAGE_BYTES_KEY)


def get_reference_image_name() -> str | None:
    """Return the uploaded reference image name."""
    return st.session_state.get(REFERENCE_IMAGE_NAME_KEY)


def set_reference_image(*, image_bytes: bytes, name: str, mime: str) -> None:
    """Store sanitized uploaded reference image data in session state."""
    st.session_state[REFERENCE_IMAGE_BYTES_KEY] = image_bytes
    st.session_state[REFERENCE_IMAGE_NAME_KEY] = name
    st.session_state[REFERENCE_IMAGE_MIME_KEY] = mime
    update_project_context(reference_image="session", reference_image_name=name)


def clear_reference_image() -> None:
    """Clear uploaded reference image data from session state and context."""
    st.session_state[REFERENCE_IMAGE_BYTES_KEY] = None
    st.session_state[REFERENCE_IMAGE_NAME_KEY] = None
    st.session_state[REFERENCE_IMAGE_MIME_KEY] = None
    st.session_state[REFERENCE_UPLOADER_VERSION_KEY] += 1
    update_project_context(reference_image=None, reference_image_name=None)


def get_reference_uploader_key() -> str:
    """Return a rotating key so the uploader can be cleared."""
    version = st.session_state.get(REFERENCE_UPLOADER_VERSION_KEY, 0)
    return f"v2_reference_upload_{version}"
