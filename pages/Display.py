# pages/Display.py
# Gallery of display PNGs with "Select"; PDQ configuration fields per your spec (no pricing/dictionary yet).

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
      .kkg-table th, .kkg-table td { padding:6px 8px; border-bottom:1px solid #f1f5f9; }
      .kkg-table th { text-align:left; color:#475569; font-weight:600; }
      .req::after { content:" *"; color:#ef4444; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Gallery scan ----------
ASSETS_ROOT = "assets/references"
ALLOWED_DIRS = {"pdq", "pallet", "sidekick", "endcap", "display", "header"}
LABEL_OVERRIDES = {
    "digital_pdq_tray": "PDQ TRAY",
    "pdq-tray-standard": "PDQ TRAY",
}

@dataclass
class OptionTile:
    key: str      # e.g., "pdq/digital_pdq_tray"
    label: str
    path: str
    category: str

def _prettify(stem: str) -> str:
    if stem in LABEL_OVERRIDES:
        return LABEL_OVERRIDES[stem]
    s = stem.replace("_", " ").replace("-", " ").strip()
    return " ".join(w.capitalize() for w in s.split())

def scan_pngs() -> List[OptionTile]:
    opts: List[OptionTile] = []
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
            path = os.path.join(cat_path, fname)
            try:
                Image.open(path).close()
            except Exception:
                continue
            opts.append(OptionTile(key=f"{cat}/{stem}", label=_prettify(stem), path=path, category=cat))
    return opts

tiles = scan_pngs()

# ---------- Header ----------
st.markdown("## Select the type of display")

# ---------- Gallery ----------
if not tiles:
    st.info(f"No PNGs found. Add images under `{ASSETS_ROOT}/<category>/...` "
            "(e.g., `assets/references/pdq/digital_pdq_tray.png`).")
else:
    cols = st.columns(3, gap="large")
    for i, t in enumerate(tiles):
        with cols[i % 3]:
            st.markdown('<div class="kkg-tile">', unsafe_allow_html=True)
            st.image(Image.open(t.path), use_column_width=False, width=320)
            st.markdown(f"<div class='kkg-label'>{t.label}</div>", unsafe_allow_html=True)
            if st.button("Select", key=f"select_{t.key}", use_container_width=True):
                st.session_state.selected_display_key = t.key
            st.markdown('</div>', unsafe_allow_html=True)

selected_key: Optional[str] = st.session_state.get("selected_display_key")

# ---------- PDQ configuration (your fields) ----------
def render_pdq_form():
    st.divider()
    st.subheader("PDQ TRAY — Configuration")

    # Ensure state bag exists
    if "pdq" not in st.session_state:
        st.session_state.pdq = {}

    # 1) FOOTPRINT (dropdown; 4 options TBD)
    footprint_options = [
        ("footprint-a", "Footprint A (TBD)"),
        ("footprint-b", "Footprint B (TBD)"),
        ("footprint-c", "Footprint C (TBD)"),
        ("footprint-d", "Footprint D (TBD)"),
    ]
    fp_labels = [lbl for _, lbl in footprint_options]
    fp_keys   = [key for key, _ in footprint_options]
    prev_fp_key = st.session_state.pdq.get("footprint", {}).get("key", fp_keys[0])
    default_fp_idx = fp_keys.index(prev_fp_key) if prev_fp_key in fp_keys else 0
    fp_choice = st.selectbox("Footprint", fp_labels, index=default_fp_idx, key="pdq_footprint")
    fp_idx = fp_labels.index(fp_choice)
    st.session_state.pdq["footprint"] = {"key": fp_keys[fp_idx], "label": fp_choice}

    # 2) HEADER (yes/no)
    header_choice = st.radio("Header", options=["Yes", "No"], horizontal=True, key="pdq_header")
    st.session_state.pdq["header"] = {"key": "header-yes" if header_choice == "Yes" else "header-no", "label": header_choice}

    # 3) DIVIDERS (strict 2 options) + manual count
    divider_options = [
        ("div-none", "None"),
        ("div-yes",  "Has Dividers"),
    ]
    div_labels = [lbl for _, lbl in divider_options]
    div_keys   = [key for key, _ in divider_options]
    prev_div_key = st.session_state.pdq.get("dividers", {}).get("key", div_keys[0])
    default_div_idx = div_keys.index(prev_div_key) if prev_div_key in div_keys else 0
    div_choice = st.selectbox("Dividers", div_labels, index=default_div_idx, key="pdq_dividers")
    div_idx = div_labels.index(div_choice)
    st.session_state.pdq["dividers"] = {"key": div_keys[div_idx], "label": div_choice}

    # Divider count (manual entry; allow 0) — kept visible as requested
    prev_cnt = int(st.session_state.pdq.get("divider_count", {}).get("value", 0))
    div_count = st.number_input("Number of dividers", min_value=0, step=1, value=prev_cnt, key="pdq_divider_count")
    st.session_state.pdq["divider_count"] = {"value": int(div_count)}

    # 4) SHIPPER (yes/no)
    shipper_choice = st.radio("Shipper", options=["Yes", "No"], horizontal=True, key="pdq_shipper")
    st.session_state.pdq["shipper"] = {"key": "shipper-yes" if shipper_choice == "Yes" else "shipper-no", "label": shipper_choice}

    # 5) ASSEMBLY (KDF/Turnkey)
    assembly_choice = st.radio("Assembly", options=["KDF", "Turnkey"], horizontal=True, key="pdq_assembly")
    st.session_state.pdq["assembly"] = {"key": "assembly-kdf" if assembly_choice == "KDF" else "assembly-turnkey", "label": assembly_choice}

    # If Turnkey → Assembly 2: product touches (0 or manual)
    if assembly_choice == "Turnkey":
        touches_mode = st.radio("Assembly 2 — Product Touches", options=["0 (none)", "Custom…"], horizontal=True, key="pdq_touches_mode")
        if touches_mode.startswith("0"):
            st.session_state.pdq["product_touches"] = {"value": 0}
        else:
            prev_touch = int(st.session_state.pdq.get("product_touches", {}).get("value", 1))
            touches_val = st.number_input("Enter number of product touches", min_value=0, step=1, value=prev_touch, key="pdq_touches_value")
            st.session_state.pdq["product_touches"] = {"value": int(touches_val)}
    else:
        # KDF: clear any previous touches to avoid confusion
        st.session_state.pdq.pop("product_touches", None)

    # --- Summary ---
    st.divider()
    st.subheader("Selections Summary (PDQ)")
    if not st.session_state.pdq:
        st.info("No selections yet.")
    else:
        st.markdown("<table class='kkg-table' width='100%'>"
                    "<tr><th>Field</th><th>Selection</th><th>Key / Value</th></tr>", unsafe_allow_html=True)
        for field_id, data in st.session_state.pdq.items():
            if "label" in data:
                st.markdown(f"<tr><td>{field_id.replace('_',' ').title()}</td><td>{data['label']}</td><td><code>{data.get('key','')}</code></td></tr>", unsafe_allow_html=True)
            else:
                st.markdown(f"<tr><td>{field_id.replace('_',' ').title()}</td><td></td><td><code>{data.get('value','')}</code></td></tr>", unsafe_allow_html=True)
        st.markdown("</table>", unsafe_allow_html=True)

# Only render PDQ config when a PDQ tile is selected
selected_key: Optional[str] = st.session_state.get("selected_display_key")
if selected_key and selected_key.startswith("pdq/"):
    render_pdq_form()
elif selected_key:
    st.divider()
    st.subheader("Configuration")
    st.caption("Fields for this display type will be added soon.")
else:
    st.caption("Select a display above to configure its details.")

st.divider()
st.page_link("Home.py", label="Back to Home", icon="🏠")
