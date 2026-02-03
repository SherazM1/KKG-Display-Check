from __future__ import annotations

import json
import os
from typing import Dict, Optional, Tuple

import streamlit as st


def load_catalog(path: str) -> Dict:
    if not os.path.isfile(path):
        st.error(f"Catalog not found at `{path}`.")
        st.stop()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to parse `{path}`: {e}")
        st.stop()


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
