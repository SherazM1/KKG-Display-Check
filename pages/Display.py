# pages/Display.py
# PDQ tray PNG preview + selection checkbox; reveals a config section when selected (no pricing, no rendering)

from __future__ import annotations
import os
import streamlit as st
from PIL import Image  # used only to verify/load PNG cleanly

# ---------- Page setup ----------
st.set_page_config(page_title="Display · KKG", layout="wide")
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] { font-family: 'Raleway', ui-sans-serif, system-ui; }
      .kkg-title { font-weight:700; font-size:22px; }
      .kkg-sub { color:#6b7280; }
      .kkg-label { text-align:center; font-weight:700; font-size:18px; color:#3b3f46; margin-top:8px; }
      .kkg-note { color:#6b7280; font-size:13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Asset path ----------
PNG_PATH = "assets/references/pdq/digital_pdq_tray.png"  # your file

# ---------- UI ----------
st.markdown("<div class='kkg-title'>PDQ Tray</div><div class='kkg-sub'>Static image selector for price estimation (no rendering).</div>", unsafe_allow_html=True)
st.divider()

left, right = st.columns([0.65, 0.35], gap="large")

with left:
    if not os.path.isfile(PNG_PATH):
        st.error(f"PNG not found at `{PNG_PATH}`. Add it to the repo and refresh.")
    else:
        # Show at native size (no explicit resizing)
        img = Image.open(PNG_PATH)
        st.image(img, caption="PDQ Tray", use_column_width=False)
        st.markdown("<div class='kkg-label'>PDQ Tray</div>", unsafe_allow_html=True)

        # Selection checkbox
        selected_default = bool(st.session_state.get("pdq_selected", False))
        pdq_selected = st.checkbox("Use this PDQ Tray for the estimate", value=selected_default)
        st.session_state.pdq_selected = pdq_selected  # persist

        st.divider()

        # Reveal fields area only when selected (placeholders for now)
        if pdq_selected:
            st.subheader("PDQ Tray — Configuration")
            st.markdown(
                "<div class='kkg-note'>Fields (size, wall style, lip graphic, dividers, material, grade, finish, assembly, weight, qty, freight) will appear here.</div>",
                unsafe_allow_html=True,
            )
            # TODO: Add real controls after you provide the exact list/order.
        else:
            st.info("Select the PDQ Tray above to configure its details.")

with right:
    st.subheader("Status")
    st.write(f"Image: {'✅ Found' if os.path.isfile(PNG_PATH) else '❌ Missing'}")
    st.write(f"Selected: {'✅ Yes' if st.session_state.get('pdq_selected') else '—'}")
    st.page_link("Home.py", label="Back to Home", icon="🏠")

st.divider()
st.caption("Next: provide the exact PDQ field list and order; we’ll drop the controls into the Configuration section.")
