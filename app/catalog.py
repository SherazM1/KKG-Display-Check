# path: app/catalog.py
from __future__ import annotations

import json
import os
from typing import Dict, Optional, Tuple

import streamlit as st


def load_catalog(path: str) -> Dict:
    """
    Load a catalog JSON from disk. Stops the Streamlit app on failure.
    """
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        st.error(f"Catalog not found at `{path}`.")
        st.stop()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to parse `{path}`: {e}")
        st.stop()


def parse_display_key(display_key: str) -> Tuple[str, str]:
    """
    Convert a gallery selection key like:
      "sidekick/sidekickpeg24" -> ("sidekick", "sidekickpeg24")
      "pdq/digital_pdq_tray"   -> ("pdq", "digital_pdq_tray")

    Returns ("", display_key) if no category delimiter is present.
    """
    if not display_key:
        return "", ""
    if "/" not in display_key:
        return "", display_key
    category, stem = display_key.split("/", 1)
    return category.strip(), stem.strip()


def catalog_path_for_display_key(
    display_key: str,
    *,
    catalog_root: str = "data/catalog",
) -> str:
    """
    Resolve the catalog JSON path for a given display_key.

    Rules:
      - PDQ always uses the shared catalog: data/catalog/pdq.json
      - Sidekick always uses the shared catalog: data/catalog/sidekick.json
        (optionally overridden by st.session_state.selected_catalog_override_path)
      - All other categories default to: data/catalog/{stem}.json
    """
    category, stem = parse_display_key(display_key)

    if category == "sidekick":
        override = st.session_state.get("selected_catalog_override_path")
        if isinstance(override, str) and override.strip():
            return os.path.expanduser(override.strip())
        return os.path.join(catalog_root, "sidekick.json")

    if category == "pdq":
        return os.path.join(catalog_root, "pdq.json")

    if not stem:
        return os.path.join(catalog_root, "catalog.json")

    return os.path.join(catalog_root, f"{stem}.json")


def load_catalog_for_display_key(
    display_key: str,
    *,
    catalog_root: str = "data/catalog",
) -> Dict:
    """
    Convenience: resolve and load the catalog for a gallery-selected display key.
    """
    path = catalog_path_for_display_key(display_key, catalog_root=catalog_root)
    return load_catalog(path)


def find_control(catalog: Dict, control_id: str) -> Optional[Dict]:
    for c in catalog.get("controls", []) or []:
        if c.get("id") == control_id:
            return c
    return None


def footprint_dims(catalog: Dict, footprint_key: str) -> Tuple[Optional[int], Optional[int]]:
    fp = find_control(catalog, "footprint")
    if not fp:
        return None, None

    for opt in fp.get("options", []) or []:
        if opt.get("key") == footprint_key:
            dims = opt.get("dims", {}) or {}
            return dims.get("width_in"), dims.get("depth_in")

    return None, None