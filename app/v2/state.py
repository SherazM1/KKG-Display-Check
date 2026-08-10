"""Shared Streamlit state helpers for the Display Check v2 shell."""

from dataclasses import replace

import streamlit as st

from app.v2.mock_data import REFERENCE_IMAGE
from app.v2.models import ProjectContext, ProjectDimensions


PROJECT_CONTEXT_KEY = "v2_project_context"


def _default_project_context() -> ProjectContext:
    """Create the default shared project context."""
    return ProjectContext(
        dimensions=ProjectDimensions(width=20, height=48, depth=12),
        reference_image=str(REFERENCE_IMAGE),
    )


def initialize_v2_state() -> None:
    """Initialize namespaced v2 session keys and widget defaults."""
    context = st.session_state.setdefault(PROJECT_CONTEXT_KEY, _default_project_context())
    st.session_state.setdefault("v2_project_name", context.project_name)
    st.session_state.setdefault("v2_display_type", context.display_type)
    st.session_state.setdefault("v2_quantity", context.quantity)
    st.session_state.setdefault("v2_print_type", context.print_type)
    st.session_state.setdefault("v2_shipping_packout", context.shipping_packout)
    st.session_state.setdefault("v2_width", context.dimensions.width)
    st.session_state.setdefault("v2_height", context.dimensions.height)
    st.session_state.setdefault("v2_depth", context.dimensions.depth)
    st.session_state.setdefault("v2_notes", context.notes)
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
