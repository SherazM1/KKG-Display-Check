# pages/Display.py
# PDQ tray PDF -> cropped, transparent image preview + selection checkbox (no pricing yet)

from __future__ import annotations
import os
from typing import Optional, Tuple

import streamlit as st

# Minimal deps only; PIL + numpy are common on Streamlit Cloud
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

from PIL import Image, ImageFilter
import numpy as np

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
    </style>
    """,
    unsafe_allow_html=True,
)

PDF_PATH = "assets/references/pdq/digital_pdq_tray.pdf"  # <- your file

# ---------- Helpers ----------
def render_pdf_first_page(pdf_path: str, scale: float = 2.0) -> Optional[Image.Image]:
    """Rasterize page 1 to RGBA. Returns None if PyMuPDF missing or file not found."""
    if fitz is None or not os.path.isfile(pdf_path):
        return None
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        doc.close()
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return img.convert("RGBA")
    except Exception:
        return None

def crop_and_make_transparent(img: Image.Image, white_thresh: int = 245, margin_px: int = 12) -> Image.Image:
    """Auto-trim white page and convert near-white to transparency. Why: show just the drawing, clean edges."""
    arr = np.asarray(img)  # RGBA
    rgb = arr[..., :3]
    # near-white mask
    near_white = (rgb[..., 0] > white_thresh) & (rgb[..., 1] > white_thresh) & (rgb[..., 2] > white_thresh)
    content = ~near_white
    if not content.any():
        return img  # nothing to trim

    ys, xs = np.where(content)
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()

    # margin
    h, w = near_white.shape
    x0 = max(0, x0 - margin_px)
    y0 = max(0, y0 - margin_px)
    x1 = min(w - 1, x1 + margin_px)
    y1 = min(h - 1, y1 + margin_px)

    cropped_rgb = rgb[y0:y1 + 1, x0:x1 + 1, :]
    cropped_near_white = near_white[y0:y1 + 1, x0:x1 + 1]

    # alpha: transparent for near white
    alpha = np.where(cropped_near_white, 0, 255).astype(np.uint8)

    # soften edges slightly to avoid halos
    alpha_img = Image.fromarray(alpha, mode="L").filter(ImageFilter.GaussianBlur(radius=0.6))
    out = Image.fromarray(cropped_rgb, mode="RGB").convert("RGBA")
    out.putalpha(alpha_img)
    return out

@st.cache_data(show_spinner=False)
def get_cropped_png_bytes(pdf_path: str, scale: float, white_thresh: int, margin_px: int) -> Optional[bytes]:
    """Cache the conversion so we don't re-render every interaction."""
    img = render_pdf_first_page(pdf_path, scale=scale)
    if img is None:
        return None
    out = crop_and_make_transparent(img, white_thresh=white_thresh, margin_px=margin_px)
    buf = st.runtime.uploaded_file_manager.io.BytesIO()
    out.save(buf, format="PNG")
    return buf.getvalue()

# ---------- UI ----------
st.markdown("<div class='kkg-title'>PDQ Tray</div><div class='kkg-sub'>Preview from your reference PDF (auto-cropped, transparent).</div>", unsafe_allow_html=True)
st.divider()

left, right = st.columns([0.65, 0.35], gap="large")

with left:
    # Tuning controls are visible for now; set and forget once you're happy.
    scale = st.slider("Render scale", 1.0, 3.0, 2.0, 0.25, help="Higher = sharper image (bigger file).")
    white_thresh = st.slider("White threshold", 220, 255, 245, 1, help="Higher removes more light pixels.")
    margin = st.slider("Trim margin (px)", 0, 40, 12, 1)

    png_bytes = get_cropped_png_bytes(PDF_PATH, scale, white_thresh, margin)

    if png_bytes is None:
        if fitz is None:
            st.error("PyMuPDF is not installed. Add `pymupdf` to requirements.txt and redeploy.")
        elif not os.path.isfile(PDF_PATH):
            st.error(f"PDF not found at `{PDF_PATH}`. Make sure the file exists and is committed.")
        else:
            st.error("Failed to render the PDF. Try lowering the render scale.")
    else:
        st.image(png_bytes, caption="PDQ Tray (cropped, transparent)", use_column_width=True)
        st.markdown("<div class='kkg-label'>PDQ Tray</div>", unsafe_allow_html=True)
        st.session_state.pdq_selected = st.checkbox("Use this PDQ Tray for the estimate", value=st.session_state.get("pdq_selected", False))

with right:
    st.subheader("Status")
    ok_pdf = os.path.isfile(PDF_PATH)
    st.write(f"PDF: {'✅ Found' if ok_pdf else '❌ Missing'}")
    st.write(f"PyMuPDF: {'✅ Installed' if fitz is not None else '❌ Not installed'}")
    st.write(f"Selected: {'✅ Yes' if st.session_state.get('pdq_selected') else '—'}")
    st.page_link("Home.py", label="Back to Home", icon="🏠")

st.divider()
st.caption("Next: we’ll stack PDQ fields (size, wall style, lip graphic, etc.) under this image. No pricing yet.")
