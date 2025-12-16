# pages/Display.py
# Gallery of display PNGs (auto-scanned) with a "Select" button; shows a configuration section after selection.

from __future__ import annotations
import os
from dataclasses import dataclass
from typing import List, Optional

import streamlit as st
from PIL import Image

# ---------- Page setup ----------
st.set_page_config(page_title="Display · KKG", layout="wide")
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] { font-family: 'Raleway', ui-sans-serif, system-ui; }
      h2 { margin-bottom: 0.25rem; }
      .kkg-sub { color:#6b7280; margin-top: 0.25rem; }
      .kkg-tile { border:1px solid #e5e7eb; border-radius:12px; padding:10px; }
      .kkg-cap { color:#6b7280; font-size:12px; margin-top:6px; text-align:center; }
      .kkg-label { text-align:center; font-weight:700; font-size:16px; color:#3b3f46; margin:6px 0 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Model ----------
ASSETS_ROOT = "assets/references"
ALLOWED_DIRS = {"pdq", "pallet", "sidekick", "endcap", "display", "header"}

@dataclass
class Option:
    key: str          # e.g., "pdq/digital_pdq_tray"
    label: str        # UI label
    path: str         # full path to PNG
    category: str     # e.g., "pdq"

def _prettify(stem: str) -> str:
    # "digital_pdq_tray" -> "Digital Pdq Tray"; "pdq-tray-standard" -> "Pdq Tray Standard"
    s = stem.replace("_", " ").replace("-", " ").strip()
    return " ".join(w.capitalize() for w in s.split())

def scan_pngs() -> List[Option]:
    opts: List[Option] = []
    if not os.path.isdir(ASSETS_ROOT):
        return opts
    for cat in sorted(os.listdir(ASSETS_ROOT)):
        cat_path = os.path.join(ASSETS_ROOT, cat)
        if not (os.path.isdir(cat_path) and cat in ALLOWED_DIRS):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if not fname.lower().endswith(".png"):
                continue
            # skip company logos or unrelated assets if they slip in
            if fname.lower().startswith(("kkg-logo", "logo")):
                continue
            stem, _ = os.path.splitext(fname)
            key = f"{cat}/{stem}"
            opts.append(Option(key=key, label=_prettify(stem), path=os.path.join(cat_path, fname), category=cat))
    return opts

options = scan_pngs()

# ---------- Header ----------
st.markdown("## Select the type of display")

# ---------- Gallery ----------
if not options:
    st.info(f"No PNGs found. Add images under `{ASSETS_ROOT}/<category>/...`. "
            "For example: `assets/references/pdq/digital_pdq_tray.png`.")
else:
    cols = st.columns(3, gap="large")
    for i, opt in enumerate(options):
        with cols[i % 3]:
            st.markdown('<div class="kkg-tile">', unsafe_allow_html=True)
            # smaller display: fixed width so cards stay compact
            try:
                img = Image.open(opt.path)
                st.image(img, use_column_width=False, width=320)
            except Exception:
                st.warning(f"Could not load: {opt.path}")
            st.markdown(f"<div class='kkg-label'>{opt.label}</div>", unsafe_allow_html=True)
            if st.button("Select", key=f"select_{opt.key}", use_container_width=True):
                st.session_state.selected_display_key = opt.key
            st.markdown('</div>', unsafe_allow_html=True)

# ---------- Selected configuration section ----------
selected_key: Optional[str] = st.session_state.get("selected_display_key")  # e.g., "pdq/digital_pdq_tray"
if selected_key:
    # find selected option
    sel = next((o for o in options if o.key == selected_key), None)
    if sel:
        st.divider()
        st.subheader(f"{sel.label} — Configuration")
        st.caption("This is where PDQ-specific fields will appear (size, wall style, lip graphic, dividers, material, etc.).")
        # TODO: add your fields here once you provide the exact list/order.
else:
    st.caption("Tip: select a display above to configure its details.")

st.divider()
st.page_link("Home.py", label="Back to Home", icon="🏠")
