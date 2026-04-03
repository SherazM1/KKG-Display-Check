from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import streamlit as st
from PIL import Image, ImageChops, ImageOps

PDQ_TYPE_BY_STEM = {
    "digital_pdq_tray": "angled",
    "clipped_pdq_tray": "clipped",
    "square_pdq_tray": "square",
    "standardclub_pdq_tray": "standard",
}

PDQ_MULTIPLIER_BY_TYPE = {
    "angled": 1.00,
    "clipped": 1.10,
    "square": 1.15,
    "standard": 1.20,
}

SIDEKICK_CATALOG_PATH = "data/catalog/sidekick.json"

SIDEKICK_INTENT_BY_STEM = {
    "sidekickpeg24": {"mode": "hooks", "width": 24, "footprint": "sk-24-hooks"},
    "sidekickpeg48": {"mode": "hooks", "width": 48, "footprint": "sk-48-hooks"},
    "sidekickshelves24": {"mode": "shelves", "width": 24},
    "sidekickshelves48": {"mode": "shelves", "width": 48},
}


@dataclass
class OptionTile:
    key: str       # e.g. "pdq/digital_pdq_tray"
    label: str
    path: str
    category: str  # e.g. "pdq"


def _prettify(stem: str, label_overrides: Optional[Dict[str, str]] = None) -> str:
    if label_overrides and stem in label_overrides:
        return label_overrides[stem]
    s = stem.replace("_", " ").replace("-", " ").strip()
    return " ".join(w.capitalize() for w in s.split())


def scan_category_pngs(
    assets_root: str,
    category: str,
    *,
    label_overrides: Optional[Dict[str, str]] = None,
) -> List[OptionTile]:
    """Return all .png tiles for one category folder under assets_root."""
    cat_path = os.path.join(assets_root, category)
    if not os.path.isdir(cat_path):
        return []

    tiles: List[OptionTile] = []
    for fname in sorted(os.listdir(cat_path)):
        if not fname.lower().endswith(".png"):
            continue
        if fname.lower().startswith(("kkg-logo", "logo")):
            continue

        stem, _ = os.path.splitext(fname)
        path = os.path.join(cat_path, fname)

        try:
            Image.open(path).close()
        except Exception:
            continue

        tiles.append(
            OptionTile(
                key=f"{category}/{stem}",
                label=_prettify(stem, label_overrides),
                path=path,
                category=category,
            )
        )
    return tiles


def _autocrop_foreground(
    img: Image.Image,
    *,
    bg_rgb: tuple[int, int, int] = (255, 255, 255),
    threshold: int = 12,
) -> Image.Image:
    """
    Crops uniform background around artwork.
    - If alpha exists, crop by alpha bbox.
    - Else crop by difference vs near-white background.
    """
    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        return rgba.crop(bbox)

    rgb = rgba.convert("RGB")
    bg = Image.new("RGB", rgb.size, bg_rgb)
    diff = ImageChops.difference(rgb, bg).convert("L")
    mask = diff.point(lambda p: 255 if p > threshold else 0, mode="L")
    bbox = mask.getbbox()
    return rgba.crop(bbox) if bbox else rgba


def fixed_preview(path: str, target_w: int = 640, target_h: int = 460) -> Image.Image:
    """
    Produces consistent-size previews by:
    1) auto-cropping whitespace
    2) containing into target box
    3) padding to exact dimensions (transparent padding)
    """
    img = Image.open(path).convert("RGBA")
    img = _autocrop_foreground(img, bg_rgb=(255, 255, 255), threshold=12)
    contained = ImageOps.contain(img, (target_w, target_h))
    return ImageOps.pad(contained, (target_w, target_h), color=(0, 0, 0, 0))


def render_tile(tile: OptionTile, *, preview_w: int = 640, preview_h: int = 460) -> None:
    """Render one tile with image + label + Select button."""
    st.image(fixed_preview(tile.path, target_w=preview_w, target_h=preview_h), use_container_width=True)
    st.markdown(f"<div class='kkg-label'>{tile.label}</div>", unsafe_allow_html=True)

    if st.button("Select", key=f"select_{tile.key}", use_container_width=True):
        st.session_state.selected_display_key = tile.key
        stem = tile.key.split("/", 1)[1] if "/" in tile.key else tile.key
        if tile.category == "pdq":
            pdq_type = PDQ_TYPE_BY_STEM.get(
                stem,
                "angled",
            )
            st.session_state.pdq_type = pdq_type
            st.session_state.pdq_multiplier = float(PDQ_MULTIPLIER_BY_TYPE.get(pdq_type, 1.00))
        elif tile.category == "sidekick":
            st.session_state.selected_catalog_override_path = SIDEKICK_CATALOG_PATH
            intent = SIDEKICK_INTENT_BY_STEM.get(stem, {})
            st.session_state.sidekick_intent = intent
            st.session_state.sidekick_mode = intent.get("mode")
            st.session_state.sidekick_width = intent.get("width")
            if "footprint" in intent:
                st.session_state.sidekick_footprint_preset = intent["footprint"]
            else:
                st.session_state.sidekick_footprint_preset = None
