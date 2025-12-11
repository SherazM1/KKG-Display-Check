# =========================
# path: pages/Extract_Drawings.py
# =========================
from __future__ import annotations
import os, io, re, uuid
from typing import List, Tuple
import numpy as np
import cv2
from PIL import Image
import streamlit as st

st.set_page_config(page_title="Extract Drawings · KKG", layout="wide")

RAW_DIR = "assets/thumbnails"     # raw book photos (your current folder with phone shots)
OUT_DIR = "assets/references"     # cleaned, single-drawing PNGs (used by Display gallery)

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\-_\s]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text or f"item-{uuid.uuid4().hex[:6]}"

def load_raw_images(folder: str) -> List[str]:
    exts = (".png", ".jpg", ".jpeg", ".webp")
    files = [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.lower().endswith(exts)]
    return files

def auto_extract(image_bgr: np.ndarray, min_area: int = 6000) -> List[np.ndarray]:
    """
    Returns list of cropped BGR subimages (one per drawing). Heuristic:
    - to gray → blur → Canny → dilate → contours
    - keep reasonably large contours → rect bounds
    - expand bounds slightly; warp if near-rect
    """
    h, w = image_bgr.shape[:2]
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 25, 25)
    edges = cv2.Canny(gray, 40, 120)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    edges = cv2.dilate(edges, kernel, iterations=2)

    cnts,_ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes: List[Tuple[int,int,int,int]] = []
    for c in cnts:
        x,y,wc,hc = cv2.boundingRect(c)
        area = wc*hc
        if area < min_area: 
            continue
        # discard near-full-page noise
        if wc > 0.95*w and hc > 0.95*h:
            continue
        # expand a bit
        pad = int(0.02 * max(w, h))
        x0 = max(0, x-pad); y0 = max(0, y-pad)
        x1 = min(w, x+wc+pad); y1 = min(h, y+hc+pad)
        boxes.append((x0,y0,x1,y1))

    # merge overlapping boxes
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
    merged = []
    for b in boxes:
        if not merged: 
            merged.append(b); continue
        x0,y0,x1,y1 = b
        X0,Y0,X1,Y1 = merged[-1]
        # overlap check
        if not (x0 > X1 or x1 < X0 or y0 > Y1 or y1 < Y0):
            merged[-1] = (min(x0,X0), min(y0,Y0), max(x1,X1), max(y1,Y1))
        else:
            merged.append(b)
    crops = []
    for x0,y0,x1,y1 in merged:
        crop = image_bgr[y0:y1, x0:x1].copy()
        if crop.size > 0:
            crops.append(crop)
    # fallback: if none detected, return full image
    if not crops:
        crops = [image_bgr]
    return crops

def white_to_alpha(bgr: np.ndarray, thresh: int = 245) -> Image.Image:
    """Convert near-white background to transparent alpha for cleaner tiles."""
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    arr = rgb.astype(np.uint8)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    mask = (gray > thresh).astype(np.uint8)*255
    # invert: lines/objects opaque
    alpha = 255 - mask
    # soften edges
    alpha = cv2.GaussianBlur(alpha, (3,3), 0)
    rgba = np.dstack([arr, alpha])
    return Image.fromarray(rgba, mode="RGBA")

def fit_thumbnail(img: Image.Image, size: int = 512, pad: int = 12) -> Image.Image:
    """Pad to square and resize for consistent gallery tiles."""
    w,h = img.size
    side = max(w,h) + pad*2
    canvas = Image.new("RGBA", (side, side), (255,255,255,0))
    canvas.paste(img, ((side-w)//2, (side-h)//2), img)
    canvas = canvas.resize((size, size), Image.LANCZOS)
    return canvas

st.header("Extract Drawings From Book Photos")
st.caption("Loads raw photos from **assets/thumbnails/**, auto-segments multiple drawings per page, and saves cleaned PNGs to **assets/references/** (used by the Display page).")

raw_files = load_raw_images(RAW_DIR)
if not raw_files:
    st.warning("No images found in `assets/thumbnails/`. Add your book photos there and refresh.")
    st.stop()

file_idx = st.selectbox("Select a source photo", options=list(range(len(raw_files))),
                        format_func=lambda i: os.path.basename(raw_files[i]))
raw_path = raw_files[file_idx]
orig = cv2.imread(raw_path)
if orig is None:
    st.error("Unable to read the selected image.")
    st.stop()

col1, col2 = st.columns([0.55, 0.45], gap="large")
with col1:
    st.subheader("Source")
    st.image(Image.open(raw_path), use_column_width=True)

with col2:
    st.subheader("Extraction")
    min_area = st.slider("Min contour area (tune to split drawings)", 3000, 40000, 12000, 1000)
    thresh = st.slider("Background removal threshold", 200, 255, 245, 1)
    crops = auto_extract(orig, min_area=min_area)
    st.caption(f"Detected regions: **{len(crops)}**")

    if crops:
        st.write("Review & label each drawing, then **Save selected** to export PNGs with transparency.")
        sel_flags, labels, previews = [], [], []
        grid = st.columns(2, gap="large")
        for i, crop in enumerate(crops):
            with grid[i % 2]:
                rgba = white_to_alpha(crop, thresh=thresh)
                thumb = fit_thumbnail(rgba, size=360)
                st.image(thumb, use_column_width=True)
                default_label = f"{os.path.splitext(os.path.basename(raw_path))[0]}-{i+1}"
                label = st.text_input("Label", value=default_label, key=f"lbl_{i}")
                save = st.checkbox("Select", key=f"sel_{i}", value=True)
                sel_flags.append(save)
                labels.append(label)
                previews.append(rgba)

        if st.button("Save selected to assets/references", type="primary"):
            saved = 0
            for save, label, rgba in zip(sel_flags, labels, previews):
                if not save: 
                    continue
                slug = slugify(label)
                out_path = os.path.join(OUT_DIR, f"{slug}.png")
                rgba.save(out_path)
                saved += 1
            st.success(f"Saved {saved} drawing(s) to {OUT_DIR}. These now appear on the Display page gallery.")

st.divider()
st.page_link("pages/Display.py", label="→ Go to Display (uses extracted drawings)", icon="🎨")