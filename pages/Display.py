# pages/Display.py
# Gallery of display PNGs (auto-scanned) with Select; configuration appears after selection.

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
      .kkg-tile { border:1px solid #e5e7eb; border-radius:12px; padding:10px; }
      .kkg-label { text-align:center; font-weight:700; font-size:16px; color:#3b3f46; margin:6px 0 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Model ----------
ASSETS_ROOT = "assets/references"
ALLOWED_DIRS = {"pdq", "pallet", "sidekick", "endcap", "display", "header"}

# Force specific nice labels (filename stem -> UI label)
LABEL_OVERRIDES = {
    "digital_pdq_tray": "PDQ TRAY",
    "pdq-tray-standard": "PDQ TRAY",
}

@dataclass
class Option:
    key: str          # e.g., "pdq/digital_pdq_tray"
    label: str        # UI label
    path: str         # full path to PNG
    category: str     # e.g., "pdq"

def _prettify(stem: str) -> str:
    if stem in LABEL_OVERRIDES:
        return LABEL_OVERRIDES[stem]
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
            if fname.lower().startswith(("kkg-logo", "logo")):
                continue
            stem, _ = os.path.splitext(fname)
            key = f"{cat}/{stem}"
            path = os.path.join(cat_path, fname)
            # Only keep tiles that actually load (no empty box)
            try:
                Image.open(path).close()
            except Exception:
                continue
            opts.append(Option(key=key, label=_prettify(stem), path=path, category=cat))
    return opts

options = scan_pngs()

# ---------- Header ----------
st.markdown("## Select the type of display")

# ---------- Gallery ----------
if not options:
    st.info(f"No PNGs found. Add images under `{ASSETS_ROOT}/<category>/...` "
            "(e.g., `assets/references/pdq/digital_pdq_tray.png`).")
else:
    cols = st.columns(3, gap="large")
    for i, opt in enumerate(options):
        with cols[i % 3]:
            st.markdown('<div class="kkg-tile">', unsafe_allow_html=True)
            img = Image.open(opt.path)
            # compact tile size
            st.image(img, use_column_width=False, width=320)
            st.markdown(f"<div class='kkg-label'>{opt.label}</div>", unsafe_allow_html=True)
            if st.button("Select", key=f"select_{opt.key}", use_container_width=True):
                st.session_state.selected_display_key = opt.key
            st.markdown('</div>', unsafe_allow_html=True)

# ---------- Selected configuration section ----------
selected_key: Optional[str] = st.session_state.get("selected_display_key")
if selected_key:
    sel = next((o for o in options if o.key == selected_key), None)
    if sel:
        st.divider()
        st.subheader(f"{sel.label} — Configuration")
        st.caption("Fields for this display will go here (we’ll add them next).")
else:
    st.caption("Select a display above to configure its details.")

st.divider()
st.page_link("Home.py", label="Back to Home", icon="🏠")
