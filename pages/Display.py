
# =========================
# path: pages/Display.py  (gallery uses extracted drawings only)
# =========================
from __future__ import annotations
import os, re
from typing import List
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Display · KKG", layout="wide")

EXTRACTED_DIR = "assets/references"  # cleaned, per-drawing PNGs (transparent BG)
os.makedirs(EXTRACTED_DIR, exist_ok=True)

def list_pngs(folder: str) -> List[str]:
    exts = (".png", ".webp")
    return [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.lower().endswith(exts)]

def pretty_label(path: str) -> str:
    name = os.path.splitext(os.path.basename(path))[0]
    name = name.replace("_"," ").replace("-"," ")
    name = re.sub(r"\s+"," ", name).strip()
    return name.title()

st.markdown("## Display Library")
st.caption("Select from **extracted drawings** (clean PNGs). These are created on the **Extract Drawings** page.")

left, right = st.columns([0.60, 0.40], gap="large")

with left:
    files = list_pngs(EXTRACTED_DIR)
    if not files:
        st.warning("No extracted drawings found in `assets/references/`. Go to Extract Drawings to create them.")
    else:
        cols = st.columns(3, gap="large")
        if "selection" not in st.session_state:
            st.session_state.selection = {"path": None, "label": None}
        for i, p in enumerate(files):
            col = cols[i % 3]
            with col:
                try:
                    img = Image.open(p)
                except Exception:
                    continue
                st.image(img, use_column_width=True)
                lab = pretty_label(p)
                st.caption(lab)
                if st.button("Select", key=f"sel_{i}", use_container_width=True):
                    st.session_state.selection = {"path": p, "label": lab}

with right:
    st.subheader("Preview")
    sel = st.session_state.get("selection", {})
    if sel.get("path"):
        st.image(Image.open(sel["path"]), use_column_width=True, caption=sel.get("label"))
        st.success("This is the cleaned drawing, not the phone photo.")
    else:
        st.info("Pick a drawing from the left to preview here.")

st.divider()
st.page_link("pages/ExtractDrawings.py", label="← Extract more drawings", icon="🪄")
